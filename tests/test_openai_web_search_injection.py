import os
import types
from typing import Any, Dict

import pytest

import core.llm_client as llm


class _StubResponses:
    def __init__(self, sink: Dict[str, Any]):
        self._sink = sink

    def create(self, **kwargs):
        self._sink.update(kwargs)
        return types.SimpleNamespace(id="resp_123", output=[])


class _StubClient:
    def __init__(self, sink: Dict[str, Any]):
        self.responses = _StubResponses(sink)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in ["ENABLE_LIVE_SEARCH", "LIVE_SEARCH_BACKEND", "OPENAI_API_KEY"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    yield


def test_injects_web_search_tool_and_overrides_model(monkeypatch, caplog):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    monkeypatch.setenv("LIVE_SEARCH_BACKEND", "openai")
    sink: Dict[str, Any] = {}
    monkeypatch.setattr(llm, "client", _StubClient(sink))

    with caplog.at_level("WARNING"):
        llm.call_openai(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "who is the ceo of openai?"}],
            api="Responses",
        )

    assert sink["model"] == "gpt-4o-mini"
    assert sink["tools"] == [{"type": "web_search_preview"}]
    assert any("Overriding to 'gpt-4o-mini'" in rec.message for rec in caplog.records)


def test_does_not_inject_when_disabled(monkeypatch):
    sink: Dict[str, Any] = {}
    monkeypatch.setattr(llm, "client", _StubClient(sink))

    llm.call_openai(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": "hello"}],
        api="Responses",
    )

    assert "tools" not in sink or sink["tools"] is None

