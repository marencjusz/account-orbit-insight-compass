
import { useEffect, useState } from "react";
import { api, type InsightResponse, type ScoredAccount } from "@/lib/api";
import { isNum, money, pct } from "@/lib/format";
import { SignalBadge } from "./SignalBadge";

const NA = <span className="text-muted-foreground">Insufficient data</span>;

function Stat({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-md border border-border px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold text-foreground tabular-nums">
        {children}
      </dd>
    </div>
  );
}

function signedMoney(value: number | null): string | null {
  if (!isNum(value)) return null;
  return `${value > 0 ? "+" : ""}${money(value)}`;
}

function OutlookRow({
  label,
  baseline,
  treated,
}: {
  label: string;
  baseline: number | null;
  treated: number | null;
}) {
  return (
    <li className="grid grid-cols-[5rem_1fr] items-center gap-3 text-sm">
      <span className="text-foreground">{label}</span>

      <div className="space-y-1.5">
        {[
          { value: baseline, color: "bg-primary/40" },
          { value: treated, color: "bg-primary" },
        ].map((bar, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              {isNum(bar.value) && (
                <span
                  className={`block h-full rounded-full ${bar.color}`}
                  style={{
                    width: `${Math.max(
                      0,
                      Math.min(100, bar.value * 100)
                    )}%`,
                  }}
                />
              )}
            </span>

            <span className="w-10 text-right font-mono text-xs tabular-nums text-muted-foreground">
              {pct(bar.value) ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </li>
  );
}

export function AccountDetails({
  account,
}: {
  account: ScoredAccount | null;
}) {
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
      .then((r) => {
        if (!cancelled) setInsight(r);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Failed to load insights."
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

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

  // Outcome probabilities without additional contact
  const loss0 = account.signals?.loss_probability ?? null;
  const stable0 = account.signals?.stable_probability ?? null;
  const expansion0 = account.signals?.expansion_probability ?? null;

  // Outcome probabilities with contact today
  const loss1 =
    isNum(loss0) && isNum(account.loss_probability_impact)
      ? loss0 - account.loss_probability_impact
      : null;

  const expansion1 =
    isNum(expansion0) && isNum(account.expansion_probability_impact)
      ? expansion0 + account.expansion_probability_impact
      : null;

  const stable1 =
    isNum(loss1) && isNum(expansion1)
      ? 1 - loss1 - expansion1
      : null;

  // Expected annualized revenue at the end of the quarter
  const expectedRevenue0 =
    isNum(account.current_revenue) &&
    isNum(account.revenue_at_risk) &&
    isNum(account.expansion_opportunity)
      ? account.current_revenue
        - account.revenue_at_risk
        + account.expansion_opportunity
      : null;

  const expectedRevenue1 =
    isNum(expectedRevenue0) &&
    isNum(account.expected_revenue_impact)
      ? expectedRevenue0 + account.expected_revenue_impact
      : null;

  return (
    <aside
      aria-label="Account details"
      className="rounded-lg border border-border bg-card"
    >
      <header className="border-b border-border px-5 py-4">
        <p className="font-mono text-xs text-muted-foreground">
          {account.account_id}
        </p>

        <h2 className="mt-0.5 text-lg font-semibold text-foreground">
          {account.account_name || "Unnamed account"}
        </h2>

        <div className="mt-2">
          <SignalBadge signal={account.primary_signal} />
        </div>
      </header>

      <div className="space-y-6 px-5 py-5">

        {/* Revenue summary - original 2x2 layout */}
        <dl className="grid grid-cols-2 gap-2">
          <Stat label="Current revenue">
            {money(account.current_revenue) ?? NA}
          </Stat>

          <Stat label="Expected · no contact">
            {money(expectedRevenue0) ?? NA}
          </Stat>

          <Stat label="Expected · contact today">
            {money(expectedRevenue1) ?? NA}
          </Stat>

          <Stat label="Estimated contact impact">
            {signedMoney(
              account.expected_revenue_impact ?? null
            ) ?? NA}
          </Stat>
        </dl>

        {/* Outcome probabilities */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Outlook estimates
          </h3>

          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-primary/40" />
              No new contact
            </span>

            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-primary" />
              Contact today
            </span>
          </div>

          <ul className="mt-4 space-y-3">
            <OutlookRow
              label="Loss"
              baseline={loss0}
              treated={loss1}
            />

            <OutlookRow
              label="Stable"
              baseline={stable0}
              treated={stable1}
            />

            <OutlookRow
              label="Expansion"
              baseline={expansion0}
              treated={expansion1}
            />
          </ul>
        </section>

        {/* Account brief */}
        <div className="border-t border-border pt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Account brief
          </h3>

          {loading && (
            <div className="mt-3 space-y-2" aria-busy="true">
              <p className="text-sm text-muted-foreground">
                Preparing brief…
              </p>
              {[100, 92, 70, 85].map((w, i) => (
                <div
                  key={i}
                  className="h-3 animate-pulse rounded bg-muted"
                  style={{ width: `${w}%` }}
                />
              ))}
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-3 rounded-md border border-risk/30 bg-risk-soft px-3 py-2 text-sm text-risk"
            >
              Could not load the brief: {error}{" "}
              <button
                className="font-medium underline"
                onClick={() => setRetry((n) => n + 1)}
              >
                Retry
              </button>
            </div>
          )}

          {insight && !loading && (
            <div className="mt-3 space-y-5">
              <p className="text-sm leading-relaxed text-foreground">
                {insight.summary || NA}
              </p>

              <BulletList
                title="Key insights"
                items={insight.insights}
              />

              <BulletList
                title="Recommended actions"
                items={insight.recommended_actions}
              />
            </div>
          )}
        </div>

      </div>
    </aside>
  );
}

function BulletList({
  title,
  items,
}: {
  title: string;
  items?: string[] | null | undefined;
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-foreground">
        {title}
      </h4>

      {items && items.length ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((t, i) => (
            <li
              key={i}
              className="flex gap-2 text-sm text-foreground"
            >
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
