from types import SimpleNamespace
from unittest.mock import patch

import config.feature_flags as ff
from core import orchestrator
from core.agents.base_agent import BaseAgent


def _stub_openai(*, model, messages, **_kw):
    return {
        "raw": SimpleNamespace(
            choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1))]
        ),
        "text": "{}",
    }


def _make_fetch(resp):
    return lambda cfg, query, agent, task: resp


def _run(monkeypatch, flag):
    monkeypatch.setattr(ff, "RAG_ENABLED", flag)
    monkeypatch.setattr(ff, "ENABLE_LIVE_SEARCH", False)
    fetch_resp = {
        "rag_snippets": ["ctx"] if flag else [],
        "web_results": [],
        "trace": {
            "rag_hits": 1 if flag else 0,
            "web_used": False,
            "backend": "none",
            "sources": 0,
            "reason": "ok",
        },
    }
    task = {"id": "T1", "role": "Exec", "title": "t", "description": "d"}

    def fake_execute(idea, tasks, agents):
        agent = BaseAgent("Exec", "gpt", "sys", "Task: {task}")
        return {"Exec": agent.run(idea, task)}

    with patch("core.orchestrator.generate_plan", return_value=[task]), patch(
        "core.orchestrator.execute_plan", fake_execute
    ), patch("core.orchestrator.compose_final_proposal", lambda idea, answers: "final"), patch(
        "dr_rd.retrieval.context.fetch_context", _make_fetch(fetch_resp)
    ), patch(
        "core.llm_client.call_openai", _stub_openai
    ), patch(
        "core.agents.base_agent.call_openai", _stub_openai
    ), patch(
        "core.agents.base_agent.fetch_context", _make_fetch(fetch_resp)
    ):
        return orchestrator.orchestrate("idea")


def test_rag_toggle(monkeypatch):
    assert _run(monkeypatch, True) == "final"
    assert _run(monkeypatch, False) == "final"
