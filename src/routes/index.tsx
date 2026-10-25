import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useRef, useState } from "react";
import { api, API_MODE, type ScoredAccount } from "@/lib/api";
import { countCsvRows } from "@/lib/csv";
import { UploadArea } from "@/components/account/UploadArea";
import { AccountList, sortAccounts, type SortKey } from "@/components/account/AccountList";
import { AccountDetails } from "@/components/account/AccountDetails";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Account Intelligence" },
      { name: "description", content: "Prioritize customer accounts and prepare for meetings with account briefs." },
      { property: "og:title", content: "Account Intelligence" },
      { property: "og:description", content: "Prioritize customer accounts and prepare for meetings." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Index,
});

const PAGE = 5;

function Index() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [rowCount, setRowCount] = useState<number | null>(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<ScoredAccount[] | null>(null);
  const [sort, setSort] = useState<SortKey>("expected_revenue_impact");
  const [visible, setVisible] = useState(PAGE);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const reqId = useRef(0);

  const sorted = useMemo(() => (accounts ? sortAccounts(accounts, sort) : []), [accounts, sort]);
  const selected = useMemo(() => accounts?.find((a) => a.account_id === selectedId) ?? null, [accounts, selectedId]);

  async function handleFile(file: File) {
    const id = ++reqId.current;
    setFileName(file.name);
    setAccounts(null);
    setSelectedId(null);
    setVisible(PAGE);
    setError(null);
    setRowCount(null);
    if (!/\.csv$/i.test(file.name) && file.type !== "text/csv") {
      setError("Please upload a .csv file.");
      return;
    }
    setProcessing(true);
    try {
      try {
        setRowCount(countCsvRows(await file.text()));
      } catch {
        /* backend will report parse issues */
      }
      const res = await api.score(file);
      if (id !== reqId.current) return;
      if (!Array.isArray(res?.accounts)) throw new Error("Unexpected response from scoring service.");
      setAccounts(res.accounts);
      setRowCount(res.accounts.length);
    } catch (e) {
      if (id !== reqId.current) return;
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      if (id === reqId.current) setProcessing(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-primary font-mono text-xs font-bold text-primary-foreground">AI</span>
            <h1 className="text-base font-semibold tracking-tight text-foreground">Account Intelligence</h1>
          </div>
          {API_MODE === "mock" && (
            <span className="rounded-full border border-border px-2.5 py-0.5 text-xs text-muted-foreground">Mock data</span>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
        <UploadArea fileName={fileName} rowCount={rowCount} processing={processing} error={error} onFile={handleFile} />

        {accounts && accounts.length === 0 && (
          <p className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
            No accounts were returned for this file.
          </p>
        )}

        {accounts && accounts.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] lg:items-start">
            <AccountList
              accounts={sorted.slice(0, visible)}
              total={sorted.length}
              sort={sort}
              onSort={setSort}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onLoadMore={() => setVisible((v) => v + PAGE)}
            />
            <div className="lg:sticky lg:top-6">
              <AccountDetails account={selected} />
            </div>
          </div>
        )}

        {!accounts && !processing && !error && (
          <p className="py-16 text-center text-sm text-muted-foreground">
            Upload a CSV of customer accounts to see who needs attention first.
          </p>
        )}
      </main>
    </div>
  );
}
