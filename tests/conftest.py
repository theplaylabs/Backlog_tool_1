"""pytest configuration for Backlog CLI project.

Provides automatic stubbing of OpenAI network calls so the test suite runs
offline by default.  If you set environment variable `RUN_LIVE_OPENAI_TESTS=1`
and have `OPENAI_API_KEY` available (from your shell or `.env`), the real API
will be used instead.
"""

import os
import sys
import types
import importlib

import pytest

import builtins

import pytest


@pytest.fixture(autouse=True)
def _maybe_stub_openai(monkeypatch):
    """Stub OpenAI unless RUN_LIVE_OPENAI_TESTS=1 and key present."""

    # Ensure env var so client init doesn't complain
    # Ensure some key for code paths that still validate its presence
    if os.getenv("RUN_LIVE_OPENAI_TESTS") == "1" and os.getenv("OPENAI_API_KEY"):
        # Real API requested
        return

    import importlib
    import backlog_cli.openai_client as oc  # already imported during collection

    def _dummy_create(*_args, **_kwargs):  # noqa: D401
        msg = types.SimpleNamespace(content='{"title":"X","difficulty":1,"description":"d","timestamp":"2025-01-01T00:00:00Z"}')
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    # Patch the helper used inside openai_client
    monkeypatch.setattr(oc, "_chat_create", _dummy_create, raising=True)

    # Additionally patch actual openai module if other code imports it
    try:
        import openai  # type: ignore
    except ModuleNotFoundError:
        openai = types.ModuleType("openai")  # type: ignore
        sys.modules["openai"] = openai
    openai = importlib.import_module("openai")  # type: ignore

    openai.OpenAIError = Exception  # type: ignore
    openai.ChatCompletion = types.SimpleNamespace(create=_dummy_create)  # type: ignore
    openai.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=_dummy_create))  # type: ignore

    yield
