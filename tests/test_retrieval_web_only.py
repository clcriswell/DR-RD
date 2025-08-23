import json
import logging
from types import SimpleNamespace
from unittest.mock import patch

import config.feature_flags as ff
from core.agents import base_agent as base_mod
from core.agents import planner_agent as planner_mod
from core.agents.base_agent import BaseAgent
from core.agents.planner_agent import run_planner
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


class DummyWeb:
    def __init__(self):
        self.called = 0

    def search_and_summarize(self, query, k, max_tokens):
        self.called += 1
        return "s1\ns2", [Source(title="t1", url="u1"), Source(title="t2", url="u2")]


def _set_web_only_flags(monkeypatch):
    for mod in (ff, base_mod, planner_mod):
        monkeypatch.setattr(mod, "RAG_ENABLED", True, raising=False)
        monkeypatch.setattr(mod, "ENABLE_LIVE_SEARCH", True, raising=False)
        monkeypatch.setattr(mod, "LIVE_SEARCH_BACKEND", "openai", raising=False)
        monkeypatch.setattr(mod, "LIVE_SEARCH_MAX_CALLS", 3, raising=False)
        monkeypatch.setattr(mod, "LIVE_SEARCH_SUMMARY_TOKENS", 256, raising=False)
        monkeypatch.setattr(mod, "VECTOR_INDEX_PRESENT", False, raising=False)
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)


def test_planner_web_only(monkeypatch, caplog):
    _set_web_only_flags(monkeypatch)
    dummy = DummyWeb()
    monkeypatch.setattr("dr_rd.retrieval.context.get_live_client", lambda b: dummy)

    captured = {}

    def fake_llm_call(_a, _b, _c, messages, **_kw):
        captured["messages"] = messages
        return SimpleNamespace(
            output_text="{}",
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0),
                )
            ],
        )

    with caplog.at_level(logging.INFO):
        with patch("core.agents.planner_agent.llm_call", fake_llm_call):
            run_planner("idea", "model")
    assert dummy.called == 1
    assert any(
        "RetrievalTrace agent=Planner" in r.message
        and "rag_hits=0" in r.message
        and "web_used=true" in r.message
        and "backend=openai" in r.message
        and "reason=no_vector_index_fallback" in r.message
        for r in caplog.records
    )
    user_content = next(m["content"] for m in captured["messages"] if m["role"] == "user")
    assert "Web Search Results" in user_content
    assert "t1" in user_content and "t2" in user_content
    assert "# RAG Knowledge" not in user_content


def test_executor_web_only(monkeypatch, caplog):
    _set_web_only_flags(monkeypatch)
    dummy = DummyWeb()
    monkeypatch.setattr("dr_rd.retrieval.context.get_live_client", lambda b: dummy)

    fake_resp = {
        "raw": SimpleNamespace(
            choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0))]
        ),
        "text": json.dumps({}),
    }
    captured = {}

    def fake_call_openai(*, messages, **_kw):
        captured["messages"] = messages
        return fake_resp

    with caplog.at_level(logging.INFO):
        with patch("core.agents.base_agent.call_openai", fake_call_openai):
            agent = BaseAgent("Exec", "gpt", "sys", "Task: {task}")
            agent.run("idea", {"id": "T1", "title": "t", "description": "d"})
    assert dummy.called == 1
    assert any(
        "RetrievalTrace agent=Exec" in r.message
        and "rag_hits=0" in r.message
        and "web_used=true" in r.message
        and "backend=openai" in r.message
        and "reason=no_vector_index_fallback" in r.message
        for r in caplog.records
    )
    user_content = next(m["content"] for m in captured["messages"] if m["role"] == "user")
    assert "Web Search Results" in user_content
    assert "t1" in user_content and "t2" in user_content
    assert "# RAG Knowledge" not in user_content
