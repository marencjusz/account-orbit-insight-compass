import { useRef, useState } from "react";

interface Props {
  fileName: string | null;
  rowCount: number | null;
  processing: boolean;
  error: string | null;
  onFile: (file: File) => void;
}

export function UploadArea({ fileName, rowCount, processing, error, onFile }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const accept = (f: File | undefined) => {
    if (f) onFile(f);
    if (input.current) input.current.value = "";
  };

  return (
    <section aria-label="CSV upload">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          accept(e.dataTransfer.files?.[0]);
        }}
        className={`flex flex-col items-center justify-between gap-4 rounded-lg border border-dashed px-6 py-6 sm:flex-row ${
          drag ? "border-primary bg-primary/5" : "border-border bg-card"
        }`}
      >
        <div className="text-center sm:text-left">
          {fileName ? (
            <>
              <p className="text-sm font-medium text-foreground">{fileName}</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {processing ? (
                  <span className="inline-flex items-center gap-2">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    Scoring{rowCount != null ? ` ${rowCount} accounts` : ""}…
                  </span>
                ) : rowCount != null ? (
                  `${rowCount} accounts`
                ) : (
                  "—"
                )}
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-foreground">Drop an accounts CSV here</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Expected columns include account_id, account_name, current_revenue, days_to_next_renewal…
              </p>
            </>
          )}
        </div>
        <button
          type="button"
          disabled={processing}
          onClick={() => input.current?.click()}
          className="shrink-0 rounded-md border border-border bg-background px-3.5 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-50"
        >
          {fileName ? "Replace CSV" : "Choose file"}
        </button>
        <input
          ref={input}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => accept(e.target.files?.[0])}
        />
      </div>
      {error && (
        <p role="alert" className="mt-3 rounded-md border border-risk/30 bg-risk-soft px-3 py-2 text-sm text-risk">
          {error}
        </p>
      )}
    </section>
  );
}
