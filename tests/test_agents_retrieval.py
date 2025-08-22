import json
from types import SimpleNamespace
from unittest.mock import patch

from core.agents.base_agent import BaseAgent
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.pipeline import ContextBundle
from dr_rd.retrieval.live_search import Source


def test_agent_populates_sources():
    bundle = ContextBundle(rag_text="snippet", web_summary="web", sources=["doc1", "url1"])
    fake_resp = {"raw": SimpleNamespace(choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0))]), "text": '{"x":1}'}
    with patch("core.agents.base_agent.collect_context", return_value=bundle), patch(
        "core.agents.base_agent.call_openai", return_value=fake_resp
    ):
        agent = BaseAgent("Test", "gpt", "sys", "Task: {task}")
        out = agent.run("idea", "do")
        data = json.loads(out)
        assert data["sources"] == ["doc1", "url1"]


def test_pipeline_respects_budget(monkeypatch):
    dummy_budget = SimpleNamespace(retrieval_calls=0, web_search_calls=1, retrieval_tokens=0, skipped_due_to_budget=0)
    monkeypatch.setattr(pipeline, "BUDGET", dummy_budget)
    cfg = {
        "rag_enabled": False,
        "live_search_enabled": True,
        "live_search_backend": "openai",
        "live_search_max_calls": 1,
        "live_search_summary_tokens": 10,
    }
    with patch("dr_rd.retrieval.live_search.OpenAIWebSearchClient.search_and_summarize", return_value=("sum", [Source("t","u")])):
        bundle = pipeline.collect_context("i", "t", cfg)
        assert bundle.web_summary == ""
        assert dummy_budget.skipped_due_to_budget == 1
