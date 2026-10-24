import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .extract import extract_batch


CACHE_PATH = (
    Path(__file__).resolve().parents[1]
    / ".cache"
    / "transcripts.json"
)


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["account_id"] = data["account_id"].astype(str)

    cache = (
        json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if CACHE_PATH.exists()
        else {}
    )

    pending = {}

    for _, row in data.iterrows():
        summary = row.get("call_transcript_summary")
        summary = summary.strip() if isinstance(summary, str) else ""

        if not summary:
            continue

        key = hashlib.sha256(summary.encode("utf-8")).hexdigest()

        if key not in cache:
            pending[row["account_id"]] = {
                "account_id": row["account_id"],
                "summary": summary,
            }

    requests = list(pending.values())

    for start in range(0, len(requests), 20):
        batch = requests[start:start + 20]

        for attempt in range(3):
            try:
                answer = extract_batch(batch)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5 * (2 ** attempt))

        received = {
            item.account_id: item.features.model_dump()
            for item in answer.accounts
        }

        requested = {item["account_id"] for item in batch}

        if received.keys() != requested or len(answer.accounts) != len(requested):
            raise RuntimeError(
                "Gemini returned unexpected or missing account IDs"
            )

        for item in batch:
            key = hashlib.sha256(
                item["summary"].encode("utf-8")
            ).hexdigest()
            cache[key] = received[item["account_id"]]

        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(cache, indent=2),
            encoding="utf-8",
        )

        print(
            f"Gemini extraction: "
            f"{min(start + 20, len(requests))}/{len(requests)}",
            flush=True,
        )

    extracted = []

    for summary in data["call_transcript_summary"]:
        summary = summary.strip() if isinstance(summary, str) else ""
        key = hashlib.sha256(summary.encode("utf-8")).hexdigest()

        extracted.append(
            cache[key] if summary else {
                "signal": "none",
                "reason": "unknown",
                "seat_change": None,
            }
        )

    data["signal"] = [e["signal"] for e in extracted]
    data["reason"] = [e["reason"] for e in extracted]

    change = pd.to_numeric(
        [e["seat_change"] for e in extracted],
        errors="coerce",
    )

    data["has_seat_change"] = np.isfinite(change).astype(int)

    seats = pd.to_numeric(data["nr_licensed_seats"], errors="coerce")
    users = pd.to_numeric(data["nr_active_users"], errors="coerce")

    data["seat_utilization"] = users.div(
        seats.where(seats > 0)
    )

    data["seat_change_ratio"] = (
        pd.Series(change, index=data.index)
        .fillna(0)
        .div(seats.where(seats > 0))
        .fillna(0)
    )

    for name in [
        "ai_usage",
        "nr_support_tickets",
        "days_to_next_renewal",
        "nr_employees",
        "current_revenue",
        "days_since_last_sales_activity",
    ]:
        data[name] = pd.to_numeric(data[name], errors="coerce")

    return data