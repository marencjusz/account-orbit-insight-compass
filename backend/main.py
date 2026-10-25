import pandas as pd

from fastapi import FastAPI, File, HTTPException, UploadFile

from .scoring.model import score_accounts
from .insights import generate_insight
from .schemas import InsightRequest, InsightResponse, ScoreResponse


app = FastAPI(title="Account Intelligence API")

app.state.accounts_df = None
app.state.raw_accounts = {}
app.state.scored_accounts = {}
app.state.insight_cache = {}

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/score", response_model=ScoreResponse)
def score(file: UploadFile = File(...)) -> ScoreResponse:

    app.state.insight_cache = {}

    df = pd.read_csv(
        file.file,
        keep_default_na=False,
        na_values=[""],
    )

    # Never use the supervised target during inference
    df = df.drop(
        columns=["revenue_end_of_quarter"],
        errors="ignore",
    )

    if df.empty or "account_id" not in df:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain accounts and account_id.",
        )

    if df["account_id"].duplicated().any():
        raise HTTPException(
            status_code=400,
            detail="Duplicate account IDs.",
        )

    results = score_accounts(df)

    # Retain information for /api/insight
    app.state.accounts_df = df
    app.state.raw_accounts = {
        row["account_id"]: row
        for row in df.fillna("").astype(str).to_dict("records")
    }
    app.state.scored_accounts = {
        item.account_id: item for item in results
    }

    return ScoreResponse(accounts=results)



@app.post("/api/insight", response_model=InsightResponse)
def insight(request: InsightRequest) -> InsightResponse:

    account_id = request.account_id

    account = app.state.raw_accounts.get(account_id)
    score = app.state.scored_accounts.get(account_id)

    if account is None or score is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found. Upload a CSV first.",
        )

    if account_id not in app.state.insight_cache:
        app.state.insight_cache[account_id] = generate_insight(
            account, score
        )

    return app.state.insight_cache[account_id]
