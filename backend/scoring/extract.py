
import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.scoring.schemas import ExtractionBatch, TranscriptFeatures
from backend.scoring.prompts import EXTRACT_PROMPT

ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT / ".cache" / "transcripts.json"


def extract_batch(accounts: list[dict]) -> ExtractionBatch:
    load_dotenv(ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
            EXTRACT_PROMPT
            + "\nACCOUNTS DATA:\n"
            + json.dumps(accounts, ensure_ascii=False)
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionBatch,
            temperature=0,
        ),
    )

    if not response.text:
        raise RuntimeError("Empty Gemini response")

    return ExtractionBatch.model_validate_json(response.text)



def extract_transcripts(
    accounts: list[dict],
    batch_size: int = 50,
) -> list[TranscriptFeatures]:

    cache = (
        json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if CACHE_PATH.exists()
        else {}
    )

    def key(account: dict) -> str:
        content = json.dumps(
            account,
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Unique, uncached accounts with nonempty summaries
    pending = {
        key(account): account
        for account in accounts
        if account["summary"] and key(account) not in cache
    }

    pending = list(pending.items())

    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]

        requests = [
            {"account_id": str(i), **account}
            for i, (_, account) in enumerate(batch)
        ]

        for attempt in range(3):
            try:
                result = extract_batch(requests)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5 * 2**attempt)

        received = {
            item.account_id: item.features
            for item in result.accounts
        }

        expected = {str(i) for i in range(len(batch))}
        if set(received) != expected or len(result.accounts) != len(batch):
            raise RuntimeError("Incomplete transcript extraction")

        for i, (hash_key, _) in enumerate(batch):
            cache[hash_key] = received[str(i)].model_dump()

        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(cache, indent=2),
            encoding="utf-8",
        )

        print(
            f"Extracted {min(start + batch_size, len(pending))}"
            f"/{len(pending)} new transcripts",
            flush=True,
        )

    empty = TranscriptFeatures(
        signal="keep",
        reason="other",
        seat_change=0,
    )

    return [
        TranscriptFeatures.model_validate(cache[key(account)])
        if account["summary"] else empty.model_copy()
        for account in accounts
    ]
