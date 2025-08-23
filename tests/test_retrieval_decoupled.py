import types
from types import SimpleNamespace

from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


class DummyClient:
    def __init__(self):
        self.called = 0

    def search_and_summarize(self, query, k, max_tokens):
        self.called += 1
        return "sum", [Source(title="t", url="u")]


class DummyRetriever:
    def __init__(self, hits):
        self._hits = hits

    def query(self, text, top_k):
        return self._hits


def _cfg():
    return {
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_max_calls": 2,
        "live_search_summary_tokens": 32,
    }


def test_no_retriever_triggers_web(monkeypatch):
    dummy = DummyClient()
    monkeypatch.setattr(pipeline, "get_live_client", lambda b: dummy)
    cfg = _cfg()
    cfg["vector_index_present"] = False
    bundle = pipeline.collect_context("idea", "task", cfg, retriever=None)
    assert dummy.called == 1
    assert bundle.meta["reason"] == "fallback_no_vector"
    assert bundle.web_summary == "sum"


def test_empty_rag_triggers_web(monkeypatch):
    dummy = DummyClient()
    monkeypatch.setattr(pipeline, "get_live_client", lambda b: dummy)
    retriever = DummyRetriever([])
    cfg = _cfg()
    cfg["vector_index_present"] = True
    bundle = pipeline.collect_context("i", "t", cfg, retriever=retriever)
    assert dummy.called == 1
    assert bundle.meta["reason"] == "no_results"


def test_budget_skip(monkeypatch):
    dummy_budget = SimpleNamespace(
        retrieval_calls=0,
        web_search_calls=2,
        retrieval_tokens=0,
        skipped_due_to_budget=0,
    )
    monkeypatch.setattr(pipeline, "BUDGET", dummy_budget)
    dummy = DummyClient()
    monkeypatch.setattr(pipeline, "get_live_client", lambda b: dummy)
    cfg = _cfg()
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(1)
    rbudget.RETRIEVAL_BUDGET.used = 1
    bundle = pipeline.collect_context("i", "t", cfg, retriever=None)
    assert dummy.called == 0
    assert bundle.meta["reason"] == "budget_exhausted"
    assert dummy_budget.skipped_due_to_budget == 1
