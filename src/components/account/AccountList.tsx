import type { ScoredAccount } from "@/lib/api";
import { isNum, money } from "@/lib/format";
import { SignalBadge } from "./SignalBadge";

export type SortKey = "priority" | "risk" | "expansion" | "urgency";

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "priority", label: "Overall priority" },
  { value: "risk", label: "Revenue at risk" },
  { value: "expansion", label: "Expansion opportunity" },
  { value: "urgency", label: "Urgency" },
];

const field: Record<SortKey, keyof ScoredAccount> = {
  priority: "priority_score",
  risk: "revenue_at_risk",
  expansion: "expansion_opportunity",
  urgency: "urgency_score",
};

/** Sort full dataset descending; missing values go last. */
export function sortAccounts(list: ScoredAccount[], key: SortKey): ScoredAccount[] {
  const f = field[key];
  return [...list].sort((a, b) => {
    const av = a[f], bv = b[f];
    const an = isNum(av), bn = isNum(bv);
    if (an && bn) return (bv as number) - (av as number);
    return an ? -1 : bn ? 1 : 0;
  });
}

function exposure(a: ScoredAccount): { label: string; value: string } | null {
  if (a.primary_signal === "expansion_opportunity" && isNum(a.expansion_opportunity))
    return { label: "Opportunity", value: money(a.expansion_opportunity)! };
  if (isNum(a.revenue_at_risk) && a.revenue_at_risk > 0) return { label: "At risk", value: money(a.revenue_at_risk)! };
  if (isNum(a.expansion_opportunity)) return { label: "Opportunity", value: money(a.expansion_opportunity)! };
  return null;
}

interface Props {
  accounts: ScoredAccount[];
  total: number;
  sort: SortKey;
  onSort: (s: SortKey) => void;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onLoadMore: () => void;
}

export function AccountList({ accounts, total, sort, onSort, selectedId, onSelect, onLoadMore }: Props) {
  return (
    <section aria-label="Prioritized accounts" className="rounded-lg border border-border bg-card">
      <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Prioritized accounts</h2>
          <p className="text-xs text-muted-foreground">
            Showing {accounts.length} of {total}
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          Sort by
          <select
            value={sort}
            onChange={(e) => onSort(e.target.value as SortKey)}
            className="rounded-md border border-border bg-background px-2 py-1.5 text-sm text-foreground"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </header>
      <ol>
        {accounts.map((a, i) => {
          const sel = a.account_id === selectedId;
          const ex = exposure(a);
          return (
            <li key={a.account_id} className="border-b border-border last:border-b-0">
              <button
                type="button"
                onClick={() => onSelect(a.account_id)}
                aria-pressed={sel}
                className={`grid w-full grid-cols-[2rem_1fr_auto] items-center gap-3 px-4 py-3 text-left transition-colors ${
                  sel ? "bg-selected shadow-[inset_3px_0_0_var(--primary)]" : "hover:bg-muted/60"
                }`}
              >
                <span className="font-mono text-xs text-muted-foreground">{i + 1}</span>
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-foreground">
                    {a.account_name || a.account_id}
                  </span>
                  <span className="mt-1 flex flex-wrap items-center gap-2">
                    <SignalBadge signal={a.primary_signal} />
                    {ex && (
                      <span className="text-xs text-muted-foreground">
                        {ex.label} <span className="font-medium text-foreground">{ex.value}</span>
                      </span>
                    )}
                  </span>
                </span>
                <span className="text-right">
                  <span className="block font-mono text-lg font-semibold tabular-nums text-foreground">
                    {isNum(a.priority_score) ? Math.round(a.priority_score) : "—"}
                  </span>
                  <span className="text-[10px] uppercase tracking-wide text-muted-foreground">priority</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      {accounts.length < total && (
        <div className="border-t border-border p-3">
          <button
            type="button"
            onClick={onLoadMore}
            className="w-full rounded-md border border-border bg-background py-2 text-sm font-medium text-foreground hover:bg-muted"
          >
            Load 5 more
          </button>
        </div>
      )}
    </section>
  );
}
