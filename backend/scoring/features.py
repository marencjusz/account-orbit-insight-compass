import numpy as np
import pandas as pd

from .extract import extract_transcripts



def prepare_scoring_data(source: pd.DataFrame) -> pd.DataFrame:

    numeric = [
        "current_revenue", "nr_employees",
        "nr_licensed_seats", "nr_active_users",
        "ai_usage", "nr_support_tickets",
        "days_to_next_renewal",
        "days_since_last_sales_activity",
    ]

    data = source[["account_id", "account_name"] + numeric].copy()

    # Data types
    data["account_id"] = data["account_id"].astype(str)
    data[numeric] = data[numeric].apply(
        pd.to_numeric, errors="coerce"
    )

    # Numerical features
    seats = data["nr_licensed_seats"]
    employees = data["nr_employees"]

    data["seat_utilization"] = data["nr_active_users"] / seats.where(seats > 0)
    data["seat_penetration"] = seats / employees.where(employees > 0)

    # Squared features
    data["seat_utilization_sq"] = data["seat_utilization"] ** 2
    data["ai_usage_sq"] = data["ai_usage"] ** 2

    # Log features
    data["log_revenue"] = np.log1p(
        data["current_revenue"].clip(lower=0)
    )
    data["log_employees"] = np.log1p(employees.clip(lower=0))
    data["log_days_since_contact"] = np.log1p(
        data["days_since_last_sales_activity"].clip(lower=0)
    )

    # Gemini extraction
    accounts = [
        {
            "summary": summary.strip(),
            "nr_employees": int(n) if pd.notna(n) else None,
            "nr_licensed_seats": int(s) if pd.notna(s) else None,
            "nr_active_users": int(u) if pd.notna(u) else None,
        }
        for summary, n, s, u in zip(
            source["call_transcript_summary"].fillna("").astype(str),
            employees,
            seats,
            data["nr_active_users"],
        )
    ]

    extracted = extract_transcripts(accounts)

    data["signal"] = [x.signal for x in extracted]
    data["reason"] = [x.reason for x in extracted]
    data["seat_change"] = pd.to_numeric(
        pd.Series([x.seat_change for x in extracted]),
        errors="coerce",
    )/seats.where(seats > 0)

    return data


def set_contact_recency(
    data: pd.DataFrame,
    days_since: float,
) -> pd.DataFrame:
    result = data.copy()

    result["days_since_last_sales_activity"] = days_since
    result["log_days_since_contact"] = np.log1p(days_since)

    return result


def prepare_training_data(source: pd.DataFrame) -> pd.DataFrame:
    data = prepare_scoring_data(source)

    end_revenue = pd.to_numeric(
        source["revenue_end_of_quarter"],
        errors="coerce",
    )

    # Keep observations with valid treatment and outcome
    valid = (
        data["current_revenue"].gt(0)
        & end_revenue.notna()
        & data["days_since_last_sales_activity"].notna()
        & data["days_since_last_sales_activity"].ge(0)
    )

    data = data.loc[valid].copy()
    end_revenue = end_revenue.loc[valid]

    # Propensity categories: 0-30, 31-60, 61-90, 91+
    data["contact_bin"] = pd.cut(
        data["days_since_last_sales_activity"],
        bins=[-np.inf, 30, 60, 90, np.inf],
        labels=[0, 1, 2, 3],
    ).astype(int)

    # Relative revenue change
    data["revenue_change"] = (
        end_revenue / data["current_revenue"] - 1
    )

    # Three outcome categories
    data["outcome"] = np.select(
        [
            data["revenue_change"].lt(-1e-6),
            data["revenue_change"].gt(1e-6),
        ],
        ["loss", "expansion"],
        default="stable",
    )

    return data

