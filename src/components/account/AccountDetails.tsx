import { useEffect, useState } from "react";
import { api, type InsightResponse, type ScoredAccount } from "@/lib/api";
import { humanizeKey, isNum, money, pct } from "@/lib/format";
import { SignalBadge } from "./SignalBadge";

const NA = <span className="text-muted-foreground">Insufficient data</span>;

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold text-foreground tabular-nums">{children}</dd>
    </div>
  );
}

export function AccountDetails({ account }: { account: ScoredAccount | null }) {
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!account) return;
    let cancelled = false;
    setInsight(null);
    setError(null);
    setLoading(true);
    api
      .insight({ account_id: account.account_id })
      .then((r) => !cancelled && setInsight(r))
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : "Failed to load insights."))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [account?.account_id, retry]);

  if (!account) {
    return (
      <aside className="flex min-h-64 items-center justify-center rounded-lg border border-dashed border-border bg-card p-6 text-center text-sm text-muted-foreground">
        Select an account to see its details and brief.
      </aside>
    );
  }

  const signals = Object.entries(account.signals ?? {}).filter(([, v]) => v !== undefined);

  return (
    <aside aria-label="Account details" className="rounded-lg border border-border bg-card">
      <header className="border-b border-border px-5 py-4">
        <p className="font-mono text-xs text-muted-foreground">{account.account_id}</p>
        <h2 className="mt-0.5 text-lg font-semibold text-foreground">{account.account_name || "Unnamed account"}</h2>
        <div className="mt-2">
          <SignalBadge signal={account.primary_signal} />
        </div>
      </header>

      <div className="space-y-6 px-5 py-5">
        <dl className="grid grid-cols-2 gap-2">
          <Stat label="Annual revenue">{money(account.current_revenue) ?? NA}</Stat>
          <Stat label="Priority score">{isNum(account.priority_score) ? `${Math.round(account.priority_score)} / 100` : NA}</Stat>
          <Stat label="Revenue at risk">{money(account.revenue_at_risk) ?? NA}</Stat>
          <Stat label="Expansion opportunity">{money(account.expansion_opportunity) ?? NA}</Stat>
        </dl>

        {signals.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Outlook estimates</h3>
            <ul className="mt-2 space-y-2">
              {signals.map(([k, v]) => (
                <li key={k} className="grid grid-cols-[7rem_1fr_3rem] items-center gap-3 text-sm">
                  <span className="text-foreground">{humanizeKey(k)}</span>
                  <span className="h-1.5 overflow-hidden rounded-full bg-muted">
                    {isNum(v) && <span className="block h-full rounded-full bg-primary/70" style={{ width: `${Math.min(100, v * 100)}%` }} />}
                  </span>
                  <span className="text-right font-mono text-xs tabular-nums text-muted-foreground">{pct(v) ?? "n/a"}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="border-t border-border pt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Account brief</h3>
          {loading && (
            <div className="mt-3 space-y-2" aria-busy="true">
              <p className="text-sm text-muted-foreground">Preparing brief…</p>
              {[100, 92, 70, 85].map((w, i) => (
                <div key={i} className="h-3 animate-pulse rounded bg-muted" style={{ width: `${w}%` }} />
              ))}
            </div>
          )}
          {error && (
            <div role="alert" className="mt-3 rounded-md border border-risk/30 bg-risk-soft px-3 py-2 text-sm text-risk">
              Could not load the brief: {error}{" "}
              <button className="font-medium underline" onClick={() => setRetry((n) => n + 1)}>
                Retry
              </button>
            </div>
          )}
          {insight && !loading && (
            <div className="mt-3 space-y-5">
              <p className="text-sm leading-relaxed text-foreground">{insight.summary || NA}</p>
              <BulletList title="Key insights" items={insight.insights} />
              <BulletList title="Recommended actions" items={insight.recommended_actions} />
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

function BulletList({ title, items }: { title: string; items?: string[] | null }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      {items && items.length ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((t, i) => (
            <li key={i} className="flex gap-2 text-sm text-foreground">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary" />
              {t}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm">{NA}</p>
      )}
    </div>
  );
}
