import logging

from core.retrieval.budget import RetrievalBudget, get_web_search_call_cap
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


def test_get_web_search_call_cap():
    cfg = {}
    assert get_web_search_call_cap(cfg) == 3  # default

    cfg = {"web_search_max_calls": 5}
    assert get_web_search_call_cap(cfg) == 5  # explicit web cap

    cfg = {"live_search_max_calls": 4}
    assert get_web_search_call_cap(cfg) == 4  # legacy field

    cfg = {"web_search_max_calls": 2, "live_search_max_calls": 9}
    assert get_web_search_call_cap(cfg) == 2  # web cap wins


def test_retrieval_budget_consumption(monkeypatch, caplog):
    cfg = {
        "live_search_enabled": True,
        "vector_index_present": False,
        "rag_top_k": 5,
        "live_search_summary_tokens": 50,
    }
    cap = get_web_search_call_cap(cfg)
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(cap)

    class DummyClient:
        def __init__(self):
            self.called = 0

        def search_and_summarize(self, query, k, max_tokens):
            self.called += 1
            return "summary", [Source(title="t", url="u")]

    dummy = DummyClient()
    monkeypatch.setattr(pipeline, "get_live_client", lambda b: dummy)

    with caplog.at_level(logging.INFO):
        bundle = pipeline.collect_context("idea", "task", cfg)
        logging.info(
            "RetrievalBudget web_search_calls=%d/%d",
            rbudget.RETRIEVAL_BUDGET.used,
            rbudget.RETRIEVAL_BUDGET.max_calls,
        )
    assert bundle.meta["web_used"] is True
    assert bundle.meta["reason"] == "fallback_no_vector"
    assert rbudget.RETRIEVAL_BUDGET.used == 1
    assert any(
        f"RetrievalBudget web_search_calls=1/{cap}" in r.message for r in caplog.records
    )
