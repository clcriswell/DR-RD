import pytest
from dr_rd.retrieval import live_search as ls
from dr_rd.retrieval.context import retrieve_context


class DummyIndex:
    present = False

    def search(self, *a, **k):
        return []


def test_openai_unavailable_falls_back_to_serpapi(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test")

    def boom(*a, **k):
        raise ls.OpenAIWebSearchUnavailable("web_search tool is not enabled")

    monkeypatch.setattr(ls.OpenAIWebSearchClient, "search_and_summarize", boom)

    def serp_ok(self, query: str, num: int = 6):
        return {
            "text": "summary",
            "sources": [{"title": "A", "url": "https://a.example"}],
        }

    monkeypatch.setattr(ls.SerpAPIWebSearchClient, "search_and_summarize", serp_ok, raising=True)

    cfg = {
        "rag_enabled": True,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "web_search_max_calls": 3,
        "exec_model": "gpt-4.1-mini",
    }

    out = retrieve_context("query", cfg, index=DummyIndex())
    assert out["web_summary"] == "summary"
    assert out["meta"]["web_search_calls_used"] == 1
    assert out["meta"]["web_search_max_calls"] == 3
    assert out["meta"]["vector_index_present"] is False
