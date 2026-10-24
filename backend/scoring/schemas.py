
from typing import Literal, Annotated, List
from pydantic import BaseModel, Field


class TranscriptFeatures(BaseModel):
    signal: Annotated[Literal[
        "churn",
        "reduce",
        "keep",
        "expand",
        "none",
    ], Field(
        description=(
            "Customer's stated subscription intention. "
            "Use 'none' if no clear intention is expressed. "
            "Do not infer an intention from dissatisfaction alone."
        )
    )]

    reason: Annotated[Literal[
        "financial_pressure",
        "low_adoption_or_roi",
        "product_issues",
        "competition",
        "business_growth",
        "organizational_change",
        "positive_product_value",
        "other",
        "unknown",
    ], Field(
        description=(
            "Main reason for the customer's situation or decision. "
            "Use 'unknown' when no reason is identifiable. "
            "Choose the single most important reason."
        )
    )]

    seat_change: Annotated[int | None, Field(
        description=(
            "Explicitly mentioned change in licensed seats. "
            "Positive for expansion, negative for reduction. "
            "None if no specific seat count is provided. "
            "Do not estimate or infer missing quantities."
        )
    )]

class AccountExtraction(BaseModel):
    account_id: str
    features: TranscriptFeatures


class ExtractionBatch(BaseModel):
    accounts: List[AccountExtraction]