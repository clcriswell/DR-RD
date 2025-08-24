from core.retrieval.budget import RetrievalBudget
from dr_rd.retrieval.context import fetch_context
from dr_rd.retrieval.live_search import OpenAIWebSearchUnavailable


def test_web_fallback_no_vector(monkeypatch):
    cfg = {
        "vector_index_present": False,
        "rag_enabled": True,
        "rag_top_k": 5,
        "live_search_enabled": True,
        "live_search_backend": "serpapi",
        "web_search_max_calls": 2,
        "web_search_calls_used": 0,
    }
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(3)

    def fake_search(role, idea, q, k=5):
        return [
            {"title": "t1", "link": "u1", "snippet": "s1"},
            {"title": "t2", "link": "u2", "snippet": "s2"},
        ]

    def boom(self, *args, **kwargs):
        raise OpenAIWebSearchUnavailable("no tool")

    monkeypatch.setenv("SERPAPI_KEY", "dummy")
    monkeypatch.setattr(
        "dr_rd.retrieval.context.OpenAIWebSearchClient.search_and_summarize", boom
    )
    monkeypatch.setattr("dr_rd.retrieval.context.search_google", fake_search)
    out = fetch_context(cfg, "q", "A", "T1")
    trace = out["trace"]
    assert trace["web_used"] is True
    assert trace["backend"] == "serpapi"
    assert trace["reason"] == "live_search_error"
    assert len(out["web_results"]) == 2
    assert cfg["web_search_calls_used"] == 1
    assert rbudget.RETRIEVAL_BUDGET.used == 1
