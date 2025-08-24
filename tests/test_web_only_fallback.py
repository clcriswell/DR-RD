import os
from core.retrieval.websearch import run_live_search, _norm_max_calls


def test_norm_max_calls_env_priority(monkeypatch):
    monkeypatch.setenv("WEB_SEARCH_MAX_CALLS", "7")
    monkeypatch.delenv("LIVE_SEARCH_MAX_CALLS", raising=False)
    assert _norm_max_calls() == 7
    monkeypatch.delenv("WEB_SEARCH_MAX_CALLS", raising=False)
    monkeypatch.setenv("LIVE_SEARCH_MAX_CALLS", "5")
    assert _norm_max_calls() == 5
    monkeypatch.delenv("LIVE_SEARCH_MAX_CALLS", raising=False)
    assert _norm_max_calls() == 3


def test_run_live_search_backend_choice_openai_fallback(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "dummy")

    from core.retrieval import websearch as ws

    orig = ws.openai_web_search

    def fail(*a, **k):
        raise ws.WebSearchError("tool_not_available")

    ws.openai_web_search = fail
    try:
        payload, reason = ws.run_live_search("test query", max_results=3, backend="openai")
        assert payload["backend"] in ("serpapi", "none")
        assert "openai_fail" in reason
    finally:
        ws.openai_web_search = orig
