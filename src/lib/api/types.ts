// Shared API contracts between the frontend and the FastAPI backend.

export type PrimarySignal =
  | "churn_risk"
  | "contraction_risk"
  | "expansion_opportunity"
  | "renewal_urgency"
  | "adoption_concern"
  | (string & {});

/** Probability estimates. Extensible: unknown keys are rendered generically. */
export interface AccountSignals {
  churn_probability?: number | null | undefined;
  contraction_probability?: number | null | undefined;
  stable_probability?: number | null | undefined;
  expansion_probability?: number | null | undefined;
  [key: string]: number | null | undefined;
}

export interface ScoredAccount {
  account_id: string;
  account_name?: string | null | undefined;
  current_revenue?: number | null | undefined;
  priority_score?: number | null | undefined;
  primary_signal?: PrimarySignal | null | undefined;
  revenue_at_risk?: number | null | undefined;
  expansion_opportunity?: number | null | undefined;
  urgency_score?: number | null | undefined;
  signals?: AccountSignals | null | undefined;
  loss_probability_impact?: number | null;
  expansion_probability_impact?: number | null;
  expected_loss_impact?: number | null;
  expected_expansion_impact?: number | null;
  expected_revenue_impact?: number | null;
}

export interface ScoreResponse {
  accounts: ScoredAccount[];
}

export interface InsightRequest {
  account_id: string;
}

export interface InsightResponse {
  summary?: string | null | undefined;
  insights?: string[] | null | undefined;
  recommended_actions?: string[] | null | undefined;
}

export interface ApiClient {
  score(file: File): Promise<ScoreResponse>;
  insight(req: InsightRequest): Promise<InsightResponse>;
}
