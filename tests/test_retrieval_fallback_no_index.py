import logging

from core.retrieval.budget import RetrievalBudget
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


class DummyClient:
    def __init__(self):
        self.called = 0

    def search_and_summarize(self, query, k, max_tokens):
        self.called += 1
        return "sum", [Source(title="t1", url="u1"), Source(title="t2", url="u2")]


def test_web_fallback_no_index(monkeypatch):
    cfg = {
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_summary_tokens": 50,
        "vector_index_present": False,
    }
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(3)
    dummy = DummyClient()
    monkeypatch.setattr(pipeline, "get_live_client", lambda b: dummy)

    bundle = pipeline.collect_context("idea", "task", cfg)
    meta = bundle.meta
    assert dummy.called == 1
    assert meta["web_used"] is True
    assert meta["reason"] == "web_only"
    assert meta["backend"] == "openai"
    assert meta["sources"] == 2
    assert rbudget.RETRIEVAL_BUDGET.used == 1
