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
  churn_probability?: number | null;
  contraction_probability?: number | null;
  stable_probability?: number | null;
  expansion_probability?: number | null;
  [key: string]: number | null | undefined;
}

export interface ScoredAccount {
  account_id: string;
  account_name?: string | null;
  current_revenue?: number | null;
  priority_score?: number | null;
  primary_signal?: PrimarySignal | null;
  revenue_at_risk?: number | null;
  expansion_opportunity?: number | null;
  urgency_score?: number | null;
  signals?: AccountSignals | null;
}

export interface ScoreResponse {
  accounts: ScoredAccount[];
}

export interface InsightRequest {
  account_id: string;
}

export interface InsightResponse {
  summary?: string | null;
  insights?: string[] | null;
  recommended_actions?: string[] | null;
}

export interface ApiClient {
  score(file: File): Promise<ScoreResponse>;
  insight(req: InsightRequest): Promise<InsightResponse>;
}
