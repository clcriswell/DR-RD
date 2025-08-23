from unittest.mock import patch

from dr_rd.retrieval.live_search import Source
from dr_rd.retrieval.pipeline import collect_context


def test_live_search_without_index():
    cfg = {
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_summary_tokens": 32,
    }
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)
    with patch(
        "dr_rd.retrieval.live_search.OpenAIWebSearchClient.search_and_summarize",
        return_value=("web", [Source("t", "u")]),
    ) as mock:
        bundle = collect_context("idea", "task", cfg, retriever=None)
        assert bundle.meta["web_used"]
        assert mock.called


def test_live_search_when_rag_empty():
    class EmptyRetriever:
        def query(self, text, top_k):
            return []

    cfg = {
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_summary_tokens": 32,
    }
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)
    with patch(
        "dr_rd.retrieval.live_search.OpenAIWebSearchClient.search_and_summarize",
        return_value=("web", [Source("t", "u")]),
    ) as mock:
        bundle = collect_context("idea", "task", cfg, retriever=EmptyRetriever())
        assert bundle.meta["web_used"]
        assert mock.called
