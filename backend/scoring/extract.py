
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.scoring.schemas import ExtractionBatch


def extract_batch(accounts: list[dict]) -> ExtractionBatch:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in the project .env"
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
            "For each account, extract exactly three structured fields "
            "from its one-sentence sales-call summary. "
            "Use only explicit information. "
            "Do not guess intentions or quantities. "
            "Use null for unknown seat changes. "
            "Return every account_id exactly once.\n"
            + json.dumps(accounts, ensure_ascii=False)
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionBatch,
            temperature=0,
        ),
    )

    if not response.text:
        raise RuntimeError("Empty Gemini extraction response")

    return ExtractionBatch.model_validate_json(response.text)