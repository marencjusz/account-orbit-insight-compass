"""Minimal local FastAPI service for CSV scoring and account insights."""

import csv
import io

from fastapi import FastAPI, File, HTTPException, UploadFile

from .mock_engine import account_insight, score_account
from .schemas import InsightRequest, InsightResponse, ScoreResponse, ScoredAccount

app = FastAPI(title="Account Intelligence API")

# Single-user, in-memory state. A new upload replaces the previous one.
app.state.raw_accounts = {}
app.state.scored_accounts = {}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/score", response_model=ScoreResponse)
async def score(file: UploadFile = File(...)) -> ScoreResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if not reader.fieldnames or "account_id" not in reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV must have an account_id column.")

        rows: dict[str, dict[str, str]] = {}
        results: list[ScoredAccount] = []
        for line_number, raw in enumerate(reader, start=2):
            if not any(value and str(value).strip() for value in raw.values()):
                continue
            if None in raw:  # More CSV values than header columns.
                raise HTTPException(status_code=400, detail=f"Invalid CSV row {line_number}.")
            row = {k: (v or "").strip() for k, v in raw.items()}
            account_id = row["account_id"]
            if not account_id:
                raise HTTPException(status_code=400, detail=f"Missing account_id at row {line_number}.")
            if account_id in rows:
                raise HTTPException(status_code=400, detail=f"Duplicate account_id: {account_id}")
            rows[account_id] = row
            results.append(score_account(row))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    if not results:
        raise HTTPException(status_code=400, detail="No account rows found in the CSV.")

    # Replace the cache only after the whole upload succeeds.
    app.state.raw_accounts = rows
    app.state.scored_accounts = {item.account_id: item for item in results}
    return ScoreResponse(accounts=results)


@app.post("/api/insight", response_model=InsightResponse)
def insight(request: InsightRequest) -> InsightResponse:
    row = app.state.raw_accounts.get(request.account_id)
    score = app.state.scored_accounts.get(request.account_id)
    if row is None or score is None:
        raise HTTPException(status_code=404, detail="Account not found. Upload a CSV first.")
    return account_insight(row, score)
