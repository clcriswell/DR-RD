import logging

from core.retrieval.budget import RetrievalBudget
from dr_rd.retrieval.context import fetch_context


def _base_cfg():
    return {
        "vector_index_present": False,
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "web_search_max_calls": 2,
        "web_search_calls_used": 0,
    }


def test_openai_web_search_used(monkeypatch):
    monkeypatch.setenv("FAISS_BOOTSTRAP_MODE", "skip")
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    cfg = _base_cfg()
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(3)

    class Src:
        def __init__(self, title, url):
            self.title = title
            self.url = url

    def fake_search(self, query, k, max_tokens, **kwargs):
        return "summary", [Src("t1", "u1")]

    monkeypatch.setattr(
        "dr_rd.retrieval.context.OpenAIWebSearchClient.search_and_summarize",
        fake_search,
    )

    out = fetch_context(cfg, "q", "A", "T1")
    trace = out["trace"]
    assert trace["web_used"] is True
    assert trace["backend"] == "openai"
    assert cfg["web_search_calls_used"] == 1


def test_openai_web_search_error(monkeypatch, caplog):
    monkeypatch.setenv("FAISS_BOOTSTRAP_MODE", "skip")
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    cfg = _base_cfg()
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(3)

    def boom(self, *args, **kwargs):
        raise RuntimeError("no tool")

    monkeypatch.setattr(
        "dr_rd.retrieval.context.OpenAIWebSearchClient.search_and_summarize",
        boom,
    )

    with caplog.at_level(logging.WARNING):
        out = fetch_context(cfg, "q", "A", "T1")
    trace = out["trace"]
    assert trace["reason"] == "live_search_error"
    assert trace["backend"] == "openai"
    assert trace["web_used"] is False
    assert cfg["web_search_calls_used"] == 0
    assert any("live_search_error" in r.message for r in caplog.records)
