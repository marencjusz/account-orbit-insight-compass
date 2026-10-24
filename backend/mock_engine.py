"""Deterministic demo results. No trained model or LLM is used here."""

import hashlib
import random

from .schemas import InsightResponse, ScoredAccount

SIGNALS = (
    "churn_risk",
    "contraction_risk",
    "expansion_opportunity",
    "renewal_urgency",
    "adoption_concern",
)


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        result = float(value.replace("$", "").replace(",", "").strip())
    except ValueError:
        return None
    return result if result == result and abs(result) != float("inf") else None


def _rng(account_id: str) -> random.Random:
    seed = int.from_bytes(hashlib.sha256(account_id.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def score_account(row: dict[str, str]) -> ScoredAccount:
    """Create fake-but-repeatable scores for an uploaded account."""
    account_id = row["account_id"]
    randomizer = _rng(account_id)
    raw = [randomizer.random() + 0.1 for _ in range(4)]
    total = sum(raw)
    probs = [round(x / total, 4) for x in raw[:3]]
    probs.append(round(1.0 - sum(probs), 4))
    churn, contraction, stable, expansion = probs

    revenue = _number(row.get("current_revenue"))
    renewal_days = _number(row.get("days_to_next_renewal"))
    urgency = (
        round(min(100, max(0, 100 - renewal_days / 3.65)))
        if renewal_days is not None
        else None
    )

    return ScoredAccount(
        account_id=account_id,
        account_name=row.get("account_name") or None,
        current_revenue=revenue,
        priority_score=round(randomizer.random() * 100),
        primary_signal=SIGNALS[randomizer.randrange(len(SIGNALS))],
        revenue_at_risk=round(revenue * (churn + 0.5 * contraction), 2)
        if revenue is not None
        else None,
        expansion_opportunity=round(revenue * expansion * 0.5, 2)
        if revenue is not None
        else None,
        urgency_score=urgency,
        signals={
            "churn_probability": churn,
            "contraction_probability": contraction,
            "stable_probability": stable,
            "expansion_probability": expansion,
        },
    )


def account_insight(row: dict[str, str], score: ScoredAccount) -> InsightResponse:
    """Simple transparent placeholders, using only uploaded input fields."""
    name = score.account_name or score.account_id
    insights: list[str] = []
    actions: list[str] = []

    renewal = _number(row.get("days_to_next_renewal"))
    if renewal is not None:
        insights.append(f"Contract renewal is in {renewal:g} days.")
        if renewal <= 90:
            actions.append("Check the renewal timeline with the account owner.")

    active = _number(row.get("nr_active_users"))
    licensed = _number(row.get("nr_licensed_seats"))
    if active is not None and licensed is not None and licensed > 0:
        insights.append(f"Active-seat utilization is {active / licensed:.0%}.")
        if active / licensed < 0.5:
            actions.append("Ask whether adoption support would be useful.")

    tickets = _number(row.get("nr_support_tickets"))
    if tickets is not None:
        insights.append(f"There are {tickets:g} open support tickets.")

    if row.get("call_transcript_summary", "").strip():
        insights.append("A sales-call summary is available for further analysis.")

    if not insights:
        insights.append("Insufficient account information for specific observations.")
    if not actions:
        actions.append("Review account context before the next meeting.")

    return InsightResponse(
        summary=(
            f"Mock brief for {name}. Scores are deterministic placeholders, not "
            "predictions. The account-specific observations below come from the uploaded CSV."
        ),
        insights=insights,
        recommended_actions=actions,
    )
