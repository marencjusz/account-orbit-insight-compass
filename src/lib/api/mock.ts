// Mock adapter: same interface as the HTTP client. Placeholder values only —
// no real scoring, ML or AI. Output is deterministic per account row.
import { parseCsv } from "../csv";
import type { ApiClient, InsightResponse, PrimarySignal, ScoredAccount } from "./types";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

function hash(str: string): number {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Deterministic pseudo-random sequence seeded by account id. */
function rng(seed: number) {
  let s = seed || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 10000) / 10000;
  };
}

function num(v: string | undefined): number | null {
  if (v == null || v === "") return null;
  const n = Number(v.replace(/[$,\s]/g, ""));
  return Number.isFinite(n) ? n : null;
}

const SIGNALS: PrimarySignal[] = [
  "churn_risk",
  "contraction_risk",
  "expansion_opportunity",
  "renewal_urgency",
  "adoption_concern",
];

function mockAccount(row: Record<string, string>, idx: number): ScoredAccount {
  const id = row['account_id'] || `ROW-${String(idx + 1).padStart(4, "0")}`;
  const r = rng(hash(id));
  const revenue = num(row['current_revenue']);
  const raw = [r(), r(), r(), r()];
  const total = raw.reduce((a, b) => a + b, 0);
  const [churn = 0, contraction = 0, stable = 0, expansion = 0] = raw.map((x) => Math.round((x / total) * 100) / 100);
  const days = num(row['days_to_next_renewal']);
  const urgency = days != null ? Math.max(0, Math.min(100, Math.round(100 - days / 3.65))) : Math.round(r() * 100);
  return {
    account_id: id,
    account_name: row['account_name'] || null,
    current_revenue: revenue,
    priority_score: Math.round(r() * 100),
    primary_signal: SIGNALS[Math.floor(r() * SIGNALS.length)],
    revenue_at_risk: revenue != null ? Math.round(revenue * (churn + contraction / 2)) : null,
    expansion_opportunity: revenue != null ? Math.round(revenue * expansion * 0.5) : null,
    urgency_score: urgency,
    signals: {
      churn_probability: churn,
      contraction_probability: contraction,
      stable_probability: stable,
      expansion_probability: expansion,
    },
  };
}

const SUMMARIES = [
  "This account shows signs of declining engagement and an approaching renewal.",
  "Usage is steady, but seat utilization leaves room for a structured adoption push.",
  "Strong product engagement suggests the account may be ready for an expansion conversation.",
  "Mixed signals: core users are active, but broader adoption across licensed seats is lagging.",
];
const INSIGHTS = [
  "Low license utilization suggests adoption challenges.",
  "Renewal is approaching.",
  "A substantial amount of annual revenue is exposed.",
  "AI feature usage is trending above peer accounts.",
  "Active users have been flat over recent periods.",
  "Support interactions may indicate friction with onboarding.",
];
const ACTIONS = [
  "Schedule a meeting with the account decision-maker.",
  "Discuss adoption obstacles and possible solutions.",
  "Prepare a renewal proposal with usage highlights.",
  "Offer an enablement session for inactive seats.",
  "Explore an upsell to additional AI capabilities.",
];

function pick<T>(arr: T[], n: number, r: () => number): T[] {
  const copy = [...arr];
  const out: T[] = [];
  while (out.length < n && copy.length) out.push(copy.splice(Math.floor(r() * copy.length), 1)[0] as T);
  return out;
}

export const mockApi: ApiClient = {
  async score(file: File) {
    const text = await file.text();
    await delay(700);
    const rows = parseCsv(text);
    if (rows.length === 0) throw new Error("No account rows found in the CSV.");
    return { accounts: rows.map(mockAccount) };
  },
  async insight({ account_id }): Promise<InsightResponse> {
    await delay(600 + (hash(account_id) % 600));
    const r = rng(hash(account_id + ":insight"));
    return {
      summary: SUMMARIES[Math.floor(r() * SUMMARIES.length)] ?? null,
      insights: pick(INSIGHTS, 3, r),
      recommended_actions: pick(ACTIONS, 2, r),
    };
  },
};
