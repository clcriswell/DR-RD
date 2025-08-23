from types import SimpleNamespace

from core.agents.base_agent import BaseAgent
from core.retrieval.budget import RetrievalBudget
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


class DummyClient:
    def __init__(self):
        self.called = 0

    def search_and_summarize(self, query, k, max_tokens):
        self.called += 1
        return "s1\ns2", [Source(title="t1", url="u1"), Source(title="t2", url="u2")]


def test_live_search_fallback(monkeypatch):
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
    monkeypatch.setattr("dr_rd.retrieval.context.get_live_client", lambda b: dummy)

    bundle = pipeline.collect_context("idea", "task", cfg, retriever=None)
    assert dummy.called == 1
    meta = bundle.meta
    assert meta["web_used"] is True
    assert meta["reason"] in {"no_vector_index_fallback", "rag_zero_hits"}

    ctx = {
        "rag_snippets": bundle.rag_snippets,
        "web_results": [{"title": s.title, "url": s.url, "snippet": ""} for s in bundle.sources],
        "trace": meta,
    }
    monkeypatch.setattr("core.agents.base_agent.fetch_context", lambda *a, **k: ctx)

    agent = BaseAgent("Exec", "gpt", "sys", "Task: {task}")
    prompt = agent._augment_prompt("start", "idea", "do task", task_id="T1")
    assert "# Web Search Results" in prompt
