
import numpy as np
import pandas as pd

from .extract import extract_transcripts


def prepare_scoring_data(df: pd.DataFrame) -> pd.DataFrame:
    source = df.reset_index(drop=True)
    data = pd.DataFrame(index=source.index)

    # Account identification and monetary baseline
    data["account_id"] = source["account_id"].astype(str)
    data["account_name"] = source["account_name"]
    data["current_revenue"] = pd.to_numeric(
        source["current_revenue"], errors="coerce"
    )

    # Product engagement
    seats = pd.to_numeric(
        source["nr_licensed_seats"], errors="coerce"
    )
    users = pd.to_numeric(
        source["nr_active_users"], errors="coerce"
    )
    employees = pd.to_numeric(
        source["nr_employees"], errors="coerce"
    )

    data["seat_utilization"] = users / seats.where(seats > 0)
    data["seat_utilization_sq"] = data["seat_utilization"] ** 2

    data["ai_usage"] = pd.to_numeric(
        source["ai_usage"], errors="coerce"
    )
    data["ai_usage_sq"] = data["ai_usage"] ** 2

    data["seat_penetration"] = (
        seats / employees.where(employees > 0)
    )

    # Support and renewal
    data["nr_support_tickets"] = pd.to_numeric(
        source["nr_support_tickets"], errors="coerce"
    )
    data["days_to_next_renewal"] = pd.to_numeric(
        source["days_to_next_renewal"], errors="coerce"
    )

    # Commercial importance
    data["log_revenue"] = np.log1p(
        data["current_revenue"].clip(lower=0)
    )
    data["log_employees"] = np.log1p(
        employees.clip(lower=0)
    )

    # Company characteristics
    for col in ("industry", "segment", "region"):
        data[col] = source[col].where(
            source[col].notna(), np.nan
        )

    # LLM-extracted transcript features
    summaries = (
        source["call_transcript_summary"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    extracted = extract_transcripts(summaries)

    data["signal"] = [x.signal for x in extracted]
    data["reason"] = [x.reason for x in extracted]

    changes = pd.to_numeric(
        pd.Series([x.seat_change for x in extracted]),
        errors="coerce",
    )

    data["has_seat_change"] = changes.notna().astype(int)
    data["seat_change_ratio"] = (
        changes.fillna(0)
        / seats.where(seats > 0)
    ).fillna(0)

    return data


def set_treatment(
    data: pd.DataFrame,
    treatment: int | None = None,
) -> pd.DataFrame:
    result = data.copy()

    if treatment is not None:
        result["treatment"] = treatment

    result["treatment_utilization"] = (
        result["treatment"] * result["seat_utilization"]
    )
    result["treatment_ai_usage"] = (
        result["treatment"] * result["ai_usage"]
    )
    result["treatment_penetration"] = (
        result["treatment"] * result["seat_penetration"]
    )

    return result


def prepare_training_data(df: pd.DataFrame) -> pd.DataFrame:
    source = df.reset_index(drop=True)
    data = prepare_scoring_data(source)

    end_revenue = pd.to_numeric(
        source["revenue_end_of_quarter"],
        errors="coerce",
    )
    days_since = pd.to_numeric(
        source["days_since_last_sales_activity"],
        errors="coerce",
    )

    # Keep observations with known treatment and outcome
    valid = (
        data["current_revenue"].gt(0)
        & end_revenue.notna()
        & days_since.notna()
    )

    data = data.loc[valid].copy()
    end_revenue = end_revenue.loc[valid]
    days_since = days_since.loc[valid]

    # Treatment assignment
    data["treatment"] = days_since.le(90).astype(int)

    # Revenue change and outcome
    data["revenue_change"] = (
        end_revenue / data["current_revenue"] - 1
    )

    data["outcome"] = np.select(
        [
            end_revenue.le(0),
            data["revenue_change"].lt(-1e-6),
            data["revenue_change"].gt(1e-6),
        ],
        ["churn", "contraction", "expansion"],
        default="stable",
    )

    return set_treatment(data)
