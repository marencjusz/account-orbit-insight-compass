"""Pydantic models matching the frontend's src/lib/api/types.ts contracts."""

from pydantic import BaseModel, Field


class ScoredAccount(BaseModel):
    account_id: str
    account_name: str | None = None
    current_revenue: float | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    primary_signal: str | None = None
    revenue_at_risk: float | None = None
    expansion_opportunity: float | None = None
    urgency_score: int | None = Field(default=None, ge=0, le=100)
    signals: dict[str, float | None] | None = None
    loss_probability_impact: float | None = None
    expansion_probability_impact: float | None = None
    expected_loss_impact: float | None = None
    expected_expansion_impact: float | None = None
    expected_revenue_impact: float | None = None


class ScoreResponse(BaseModel):
    accounts: list[ScoredAccount]


class InsightRequest(BaseModel):
    account_id: str


class InsightResponse(BaseModel):
    summary: str | None = None
    insights: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
