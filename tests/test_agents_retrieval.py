import json
import logging
from types import SimpleNamespace
from unittest.mock import patch

from core.agents.base_agent import BaseAgent
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


def test_agent_populates_sources(caplog):
    ctx = {
        "rag_snippets": ["snippet"],
        "web_results": [
            {"title": "doc1", "url": "", "snippet": ""},
            {"title": "url1", "url": "", "snippet": ""},
        ],
        "trace": {
            "rag_hits": 1,
            "web_used": True,
            "backend": "openai",
            "sources": 2,
            "reason": "ok",
        },
    }
    fake_resp = {
        "raw": SimpleNamespace(
            choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0))]
        ),
        "text": '{"x":1}',
    }
    with caplog.at_level(logging.INFO):
        with patch("core.agents.base_agent.fetch_context", return_value=ctx), patch(
            "core.agents.base_agent.call_openai", return_value=fake_resp
        ):
            agent = BaseAgent("Test", "gpt", "sys", "Task: {task}")
            out = agent.run("idea", {"id": "T1", "title": "t", "description": "d"})
            data = json.loads(out)
            assert data["sources"] == ["doc1", "url1"]
    assert any("RetrievalTrace" in r.message for r in caplog.records)


def test_pipeline_respects_budget(monkeypatch):
    dummy_budget = SimpleNamespace(
        retrieval_calls=0,
        web_search_calls=1,
        retrieval_tokens=0,
        skipped_due_to_budget=0,
    )
    monkeypatch.setattr("dr_rd.retrieval.context.BUDGET", dummy_budget)
    cfg = {
        "rag_enabled": False,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_summary_tokens": 10,
    }
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(1)
    rbudget.RETRIEVAL_BUDGET.used = 1
    with patch(
        "dr_rd.retrieval.live_search.OpenAIWebSearchClient.search_and_summarize",
        return_value=("sum", [Source("t", "u")]),
    ):
        bundle = pipeline.collect_context("i", "t", cfg)
        assert bundle.web_summary is None
        assert bundle.meta["reason"] == "budget_exhausted"
        assert dummy_budget.skipped_due_to_budget == 1
