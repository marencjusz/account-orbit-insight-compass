
from typing import Literal, Annotated, List
from pydantic import BaseModel, Field


class TranscriptFeatures(BaseModel):
    signal: Annotated[Literal[
        "churn", "reduce", "keep", "expand",
    ], Field(description=(
        "Customer subscription intention, meaning what would they do without intervention. "
        "Viable categories: "
        "churn = very likely cancellation or nonrenewal; "
        "reduce = negative sentiment, short of explicitly considering churn but "
        "implying some dissatisfaction or pressure; "
        "keep = unchanged subscription or no clear intention; "
        "positive = positive sentiment, with no direct intent to immediately expand, "
        "but leaning this way and can be persuadable; "
        "expand = explicitly stated aim of subscription increase. "
        "Do reasonable but cautious inference from provided transcript. If uncertain, "
        "return keep or weaker signal (eg reduce not churn for noegative sentiment but "
        "not exactly stated churn intent)."
    ))]
    reason: Annotated[Literal[
        "commercial", "product", "other",
    ], Field(description=(
        "Category of stated reason for main signal: "
        "commercial: reasons not related to product but to commercial "
        "situation of the comapny (both positive and negative) like budget, "
        "competition, restructuring, growth; "
        "product = reasons related to product itself: adoption, ROI, technical problems; "
        "other = no identifiable reason or visibly distinct to the above."
    ))]
    seat_change: Annotated[int, Field(description=(
        "Number of licensed seats to add (positive) or remove (negative). "
        "Only change relative tu current level, interpreted as what would "
        "likely happen if there is no intervention. Cautious inference is permitted, eg. "
        "for churn intent, return or current seats; for reduction/expansion "
        "try to infer likely scale based on number of employees/licenced seats/used licences. "
        "You can also use other items in the batch to help infer possible scale. "
        "Return 0 if not stated and cannot be inferred (eg very cautious positive sentiment that "
        "if not persuaded, would maybe order some new licences but not in the immediatge future), "
        "or if intent is to keep current seats."
    ))]


class AccountExtraction(BaseModel):
    account_id: str
    features: TranscriptFeatures


class ExtractionBatch(BaseModel):
    accounts: list[AccountExtraction]
