import json
from types import SimpleNamespace

import pytest

import backlog_cli.openai_client as oc


class DummyChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


@pytest.fixture()
def mock_chat(monkeypatch):
    """Patch internal oc._chat_create helper to return controlled data."""

    def _factory(content: str):
        def _create(**_kwargs):  # noqa: D401
            return DummyResponse(content)

        return _create

    def _setter(return_json: dict):
        json_text = json.dumps(return_json)
        monkeypatch.setattr(oc, "_chat_create", _factory(json_text), raising=True)

    return _setter


def test_call_openai_success(mock_chat):
    data = {
        "title": "Add OAuth login flow",
        "difficulty": 3,
        "description": "Implement OAuth login flow for users.",
        "timestamp": "2025-06-17T18:00:00Z",
    }
    mock_chat(data)
    result = oc.call_openai("dummy idea")
    assert result == data


def test_call_openai_invalid_json(mock_chat):
    mock_chat({"not": "schema"})
    with pytest.raises(ValueError):
        oc.call_openai("bad idea")
