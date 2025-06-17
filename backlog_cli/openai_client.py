"""Utilities for calling OpenAI and converting raw dictation to structured backlog JSON."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Final

import openai

logger = logging.getLogger(__name__)

# Ensure compatibility across openai package versions
try:
    OpenAIError = openai.OpenAIError  # openai>=1.0.0
except AttributeError:  # pragma: no cover – fallback for older versions
    from openai.error import OpenAIError  # type: ignore

# ---------------------------------------------------------------------------
# Prompt pieces
# ---------------------------------------------------------------------------
_TITLE_GOOD_EXAMPLES: Final[str] = (
    "Add OAuth login flow; Refactor payment adapter module; Improve CSV import performance"
)

_RUBRIC: Final[str] = (
    "1 = Tiny tweak (\u226430 min); 2 = Small feature (\u22642 h); 3 = Medium feature (\u22641 day); "
    "4 = Large feature (1-3 days); 5 = Complex new module (>3 days)"
)

_SYSTEM_MESSAGE: Final[str] = (
    "You are a senior developer assisting in backlog grooming. "
    "Given a raw dictation line, respond with **ONLY** valid JSON matching this schema:\n"
    "{\n  \"title\": str,  # 5-6 word git-style imperative\n  \"difficulty\": int,  # 1-5 per rubric below\n  \"description\": str,  # cleaned full text\n  \"timestamp\": str  # ISO-8601 in UTC\n}\n\n"
    "Rules:\n"
    "- Use these good title examples as style reference: "
    f"{_TITLE_GOOD_EXAMPLES}.\n"
    "- Difficulty rubric: " + _RUBRIC + "\n"
    "- Do not add fields. Reply with JSON only."
)

MODEL_DEFAULT: Final[str] = os.getenv("BACKLOG_MODEL", "gpt-3.5-turbo")
_RETRY_ATTEMPTS: Final[int] = 2

# Simple in-memory cache mapping (model, prompt) -> parsed JSON response
_CACHE: dict[tuple[str, str], dict] = {}

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def sanitize_dictation(text: str) -> str:
    """Trim and normalise whitespace in the dictation string."""
    return " ".join(text.strip().split())


def call_openai(dictation: str, *, model: str | None = None) -> dict:  # noqa: D401
    """Call OpenAI chat completion and return parsed JSON dict.

    Retries up to 2 times on API error or malformed JSON.
    """
    if not dictation.strip():
        raise ValueError("Empty dictation provided")

    model = model or MODEL_DEFAULT

    prompt_user = sanitize_dictation(dictation)

    # Quick in-memory cache to avoid duplicate API calls in same session
    _cache_key = (model, prompt_user)
    if _cache_key in _CACHE:
        return _CACHE[_cache_key]

    for attempt in range(1, _RETRY_ATTEMPTS + 2):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": _SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt_user},
                ],
            )
            content = response.choices[0].message.content  # type: ignore[index]
            data = json.loads(content)
            _validate_schema(data)
            _CACHE[_cache_key] = data
            return data
        except (OpenAIError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("OpenAI attempt %s failed: %s", attempt, exc)
            if attempt > _RETRY_ATTEMPTS:
                raise
            time.sleep(2 ** attempt)  # simple exponential back-off
    # Should never reach here
    raise RuntimeError("OpenAI call failed after retries")


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _validate_schema(data: dict) -> None:
    """Basic schema validation for OpenAI response."""
    required = {"title": str, "difficulty": int, "description": str, "timestamp": str}
    for key, typ in required.items():
        if key not in data:
            raise ValueError(f"Missing key '{key}' in response JSON")
        if not isinstance(data[key], typ):
            raise ValueError(f"Field '{key}' expected {typ.__name__}, got {type(data[key]).__name__}")
    if not 1 <= data["difficulty"] <= 5:
        raise ValueError("difficulty must be between 1 and 5")
