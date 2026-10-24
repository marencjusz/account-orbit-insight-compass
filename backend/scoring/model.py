from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import prepare_features
from backend.schemas import ScoredAccount


MODEL_PATH = Path(__file__).with_name("model.joblib")

P_NUM = ["nr_employees"]
P_CAT = ["industry", "segment", "region"]

O_NUM = [
    "seat_utilization",
    "ai_usage",
    "nr_support_tickets",
    "days_to_next_renewal",
    "seat_change_ratio",
    "has_seat_change",
    "treatment",
]

O_CAT = [
    "signal",
    "reason",
    "treatment_signal",
    "treatment_reason",
]

OUTCOMES = ["churn", "contraction", "stable", "expansion"]


def pipeline(nums, cats):
    preprocessing = ColumnTransformer([
        (
            "numbers",
            Pipeline([
                ("fill", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]),
            nums,
        ),
        (
            "categories",
            Pipeline([
                ("fill", SimpleImputer(
                    strategy="constant",
                    fill_value="unknown",
                )),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]),
            cats,
        ),
    ])

    return Pipeline([
        ("features", preprocessing),
        ("classifier", LogisticRegression(max_iter=1000)),
    ])


def set_treatment(data: pd.DataFrame, treatment: int) -> pd.DataFrame:
    x = data.copy()

    x["treatment"] = treatment
    x["treatment_signal"] = np.where(
        treatment == 1, x["signal"], "untreated"
    )
    x["treatment_reason"] = np.where(
        treatment == 1, x["reason"], "untreated"
    )

    return x


def expected_fraction(probs, classes, magnitudes, treatment):
    values = {
        "churn": 0.0,
        "contraction": 1 + magnitudes["contraction"][treatment],
        "stable": 1.0,
        "expansion": 1 + magnitudes["expansion"][treatment],
    }

    return probs @ np.array([values[c] for c in classes])


def train_model(df: pd.DataFrame) -> None:
    if "revenue_end_of_quarter" not in df:
        raise ValueError("Training requires revenue_end_of_quarter")

    data = prepare_features(df)

    data["revenue_end_of_quarter"] = pd.to_numeric(
        data["revenue_end_of_quarter"],
        errors="coerce",
    )

    data = data.dropna(subset=[
        "current_revenue",
        "revenue_end_of_quarter",
        "days_since_last_sales_activity",
    ])

    data = data[data["current_revenue"] > 0].copy()

    # Observational treatment proxy
    data["treatment"] = (
        data["days_since_last_sales_activity"] <= 90
    ).astype(int)

    delta = (
        data["revenue_end_of_quarter"] / data["current_revenue"] - 1
    )

    # Four-category supervised outcome
    data["outcome"] = np.select(
        [
            data["revenue_end_of_quarter"] <= 0,
            delta < -1e-6,
            delta > 1e-6,
        ],
        ["churn", "contraction", "expansion"],
        default="stable",
    )

    # Propensity model
    propensity = pipeline(P_NUM, P_CAT)
    propensity.fit(data, data["treatment"])

    classes = propensity.named_steps["classifier"].classes_
    e = propensity.predict_proba(data)[:, list(classes).index(1)]

    # Inverse propensity weights, clipped
    e = np.clip(e, 0.1, 0.9)
    t = data["treatment"].to_numpy()

    weights = np.where(t == 1, 1 / e, 1 / (1 - e))
    weights /= weights.mean()

    # Treatment interactions with transcript signals
    data["treatment_signal"] = np.where(
        t == 1, data["signal"], "untreated"
    )
    data["treatment_reason"] = np.where(
        t == 1, data["reason"], "untreated"
    )

    # Weighted multinomial outcome model
    outcome = pipeline(O_NUM, O_CAT)

    outcome.fit(
        data,
        data["outcome"],
        classifier__sample_weight=weights,
    )

    # Conditional magnitude estimates, shrunk toward pooled means
    magnitudes = {}

    for label in ("contraction", "expansion"):
        relevant = data["outcome"] == label
        pooled = float(delta.loc[relevant].mean())

        magnitudes[label] = {}

        for tr in (0, 1):
            values = delta.loc[
                relevant & (data["treatment"] == tr)
            ]

            magnitudes[label][tr] = float(
                (values.sum() + 10 * pooled) / (len(values) + 10)
            )

    joblib.dump(
        {
            "propensity": propensity,
            "outcome": outcome,
            "magnitudes": magnitudes,
        },
        MODEL_PATH,
    )

    print(
        f"Model saved: {MODEL_PATH}\n"
        f"Training accounts: {len(data)}\n"
        f"Outcomes: {data.outcome.value_counts().to_dict()}"
    )


def score_accounts(df: pd.DataFrame) -> list[ScoredAccount]:
    # Only load model artifacts created by this project.
    artifact = joblib.load(MODEL_PATH)

    data = prepare_features(df)

    outcome = artifact["outcome"]
    magnitudes = artifact["magnitudes"]
    classes = outcome.named_steps["classifier"].classes_

    # Counterfactual outcome distributions
    p0 = outcome.predict_proba(set_treatment(data, 0))
    p1 = outcome.predict_proba(set_treatment(data, 1))

    revenue = (
        data["current_revenue"]
        .fillna(0)
        .clip(lower=0)
        .to_numpy()
    )

    r0 = revenue * expected_fraction(
        p0, classes, magnitudes, 0
    )
    r1 = revenue * expected_fraction(
        p1, classes, magnitudes, 1
    )

    # Estimated nonnegative intervention value
    uplift = np.maximum(r1 - r0, 0)
    max_uplift = max(float(uplift.max()), 1e-9)

    indices = {
        label: list(classes).index(label)
        for label in OUTCOMES
    }

    scores = []

    for i, row in data.reset_index(drop=True).iterrows():
        p = {
            label: float(p0[i, indices[label]])
            for label in OUTCOMES
        }

        money = float(revenue[i])
        has_revenue = pd.notna(row["current_revenue"])

        risk = money * (
            p["churn"]
            - magnitudes["contraction"][0] * p["contraction"]
        )

        expansion = (
            money
            * p["expansion"]
            * magnitudes["expansion"][0]
        )

        renewal = row["days_to_next_renewal"]

        urgency = (
            int(round(np.clip(
                100 * (1 - renewal / 365), 0, 100
            )))
            if pd.notna(renewal)
            else None
        )

        if p["churn"] > 0.25:
            signal = "churn_risk"
        elif p["contraction"] > 0.20:
            signal = "contraction_risk"
        elif p["expansion"] > 0.5:
            signal = "expansion_opportunity"
        elif pd.notna(renewal) and renewal <= 60:
            signal = "renewal_urgency"
        elif (
            pd.notna(row["seat_utilization"])
            and row["seat_utilization"] < 0.5
        ):
            signal = "adoption_concern"
        else:
            signal = "expansion_opportunity"

        scores.append(ScoredAccount(
            account_id=str(row["account_id"]),
            account_name=(
                str(row["account_name"])
                if pd.notna(row.get("account_name"))
                else None
            ),
            current_revenue=money if has_revenue else None,
            priority_score=(
                int(round(100 * uplift[i] / max_uplift))
                if has_revenue else None
            ),
            primary_signal=signal,
            revenue_at_risk=round(risk, 2) if has_revenue else None,
            expansion_opportunity=(
                round(expansion, 2) if has_revenue else None
            ),
            urgency_score=urgency,
            signals={
                f"{k}_probability": round(v, 4)
                for k, v in p.items()
            },
        ))

    return scores