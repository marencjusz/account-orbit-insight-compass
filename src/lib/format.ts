export const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

export function money(v: number | null | undefined): string | null {
  if (!isNum(v)) return null;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

export function pct(v: number | null | undefined): string | null {
  return isNum(v) ? `${Math.round(v * 100)}%` : null;
}

export const SIGNAL_LABELS: Record<string, string> = {
  churn_risk: "Churn Risk",
  contraction_risk: "Contraction Risk",
  expansion_opportunity: "Expansion Opportunity",
  renewal_urgency: "Renewal Urgency",
  adoption_concern: "Adoption Concern",
};

export function signalLabel(s: string | null | undefined): string {
  if (!s) return "Unclassified";
  return SIGNAL_LABELS[s] ?? s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function signalTone(s: string | null | undefined): "risk" | "warn" | "good" | "neutral" {
  if (s === "churn_risk" || s === "contraction_risk") return "risk";
  if (s === "renewal_urgency" || s === "adoption_concern") return "warn";
  if (s === "expansion_opportunity") return "good";
  return "neutral";
}

export function humanizeKey(k: string): string {
  return k.replace(/_probability$/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
