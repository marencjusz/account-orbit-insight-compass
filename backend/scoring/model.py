from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import (
    prepare_scoring_data,
    prepare_training_data,
    set_contact_recency,
)

from backend.schemas import ScoredAccount


MODEL_PATH = Path(__file__).with_name("model.joblib")

P_NUM = [
    "seat_utilization",
    "seat_utilization_sq",
    "ai_usage",
    "ai_usage_sq",
    "seat_penetration",
    "nr_support_tickets",
    "days_to_next_renewal",
    "log_revenue",
    "log_employees",
]

P_CAT = []

O_NUM = [
    "seat_utilization",
    "ai_usage",
    "nr_support_tickets",
    "days_to_next_renewal",
    "log_days_since_contact",
]

O_CAT = [
    "signal",
    "reason",
]

OUTCOMES = ["churn", "contraction", "stable", "expansion"]

M_NUM = [
    "log_days_since_contact",
    "seat_change_ratio",
    "has_seat_change",
    "seat_utilization",
]

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


def expected_fraction(probs, classes, magnitudes):
    indices = {
        label: list(classes).index(label)
        for label in OUTCOMES
    }

    return (
        probs[:, indices["stable"]]
        + probs[:, indices["contraction"]]
          * (1 - magnitudes["contraction"])
        + probs[:, indices["expansion"]]
          * (1 + magnitudes["expansion"])
    )



def fit_propensity_model(
    data: pd.DataFrame,
) -> tuple[Pipeline, np.ndarray]:

    model = pipeline(P_NUM, P_CAT)
    model.fit(data, data["contact_bin"])

    # Probability of each of the four contact-recency bins
    probabilities = model.predict_proba(data)

    bins = data["contact_bin"].to_numpy(dtype=int)
    observed_probabilities = probabilities[
        np.arange(len(data)), bins
    ]

    # Marginal frequency of each bin
    frequencies = np.bincount(bins, minlength=4) / len(bins)

    # Stabilized inverse propensity weights
    weights = (
        frequencies[bins]
        / np.maximum(observed_probabilities, 1e-6)
    )

    # Limit extreme observations
    weights = np.minimum(weights, 5.0)
    weights /= weights.mean()

    return model, weights


def fit_outcome_model(
    data: pd.DataFrame,
    weights: np.ndarray,
) -> Pipeline:

    model = pipeline(O_NUM, O_CAT)

    model.fit(
        data,
        data["outcome"],
        classifier__sample_weight=weights,
    )

    return model


def fit_magnitude_models(
    data: pd.DataFrame,
    weights: np.ndarray,
) -> dict[str, Pipeline]:

    models = {}

    for outcome in ("loss", "expansion"):
        relevant = data["outcome"] == outcome

        model = Pipeline([
            ("features", ColumnTransformer([
                ("numeric", Pipeline([
                    ("fill", SimpleImputer(strategy="median")),
                ]), M_NUM),
                ("categorical", OneHotEncoder(
                    handle_unknown="ignore"
                ), ["signal"]),
            ])),
            ("regressor", LinearRegression()),
        ])

        model.fit(
            data.loc[relevant],
            data.loc[relevant, "revenue_change"].abs(),
            regressor__sample_weight=weights[relevant.to_numpy()],
        )

        models[outcome] = model

    return models


def predict_magnitudes(
    models: dict[str, Pipeline],
    data: pd.DataFrame,
) -> dict[str, np.ndarray]:

    contraction = models["contraction"].predict(data)
    expansion = models["expansion"].predict(data)

    return {
        "contraction": np.clip(contraction, 0, 1),
        "expansion": np.maximum(expansion, 0),
    }


def train_model(df: pd.DataFrame) -> None:
    data = prepare_training_data(df)

    propensity, weights = fit_propensity_model(data)
    outcome = fit_outcome_model(data, weights)
    magnitudes = fit_magnitude_models(data, weights)

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
    artifact = joblib.load(MODEL_PATH)

    data = prepare_scoring_data(df)
    outcome = artifact["outcome"]
    magnitudes = artifact["magnitudes"]
    classes = outcome.named_steps["classifier"].classes_

    # Counterfactual datasets
    x0 = data
    x1 = set_contact_recency(data, 0)

    # Predict outcome probabilities under each treatment
    p0 = outcome.predict_proba(x0)
    p1 = outcome.predict_proba(x1)

    # Predict account-specific revenue change magnitudes
    m0 = predict_magnitudes(magnitudes, x0)
    m1 = predict_magnitudes(magnitudes, x1)

    revenue = (
        data["current_revenue"]
        .fillna(0)
        .clip(lower=0)
        .to_numpy()
    )

    # Expected revenue with and without intervention
    r0 = revenue * expected_fraction(p0, classes, m0)
    r1 = revenue * expected_fraction(p1, classes, m1)

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

        # Expected financial exposure without intervention
        risk = money * (
            p["churn"]
            + p["contraction"] * m0["contraction"][i]
        )

        # Expected expansion value without intervention
        expansion = (
            money
            * p["expansion"]
            * m0["expansion"][i]
        )

        renewal = row["days_to_next_renewal"]

        urgency = (
            int(round(np.clip(
                100 * (1 - renewal / 365), 0, 100
            )))
            if pd.notna(renewal)
            else None
        )

        # Primary attention signal
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
            revenue_at_risk=(
                round(float(risk), 2) if has_revenue else None
            ),
            expansion_opportunity=(
                round(float(expansion), 2) if has_revenue else None
            ),
            urgency_score=urgency,
            signals={
                f"{k}_probability": round(v, 4)
                for k, v in p.items()
            },
        ))

    return scores
