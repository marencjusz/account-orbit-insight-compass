import type { ApiClient, InsightRequest, InsightResponse, ScoreResponse } from "./types";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

/** Real HTTP client. Relative URLs so it works on the same origin as FastAPI. */
export const httpApi: ApiClient = {
  async score(file: File) {
    const form = new FormData();
    form.append("file", file);
    return handle<ScoreResponse>(await fetch("/api/score", { method: "POST", body: form }));
  },
  async insight(req: InsightRequest) {
    return handle<InsightResponse>(
      await fetch("/api/insight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      }),
    );
  },
};
