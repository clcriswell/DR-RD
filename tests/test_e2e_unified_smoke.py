import logging
from types import SimpleNamespace
from unittest.mock import patch

import config.feature_flags as ff
from core.agents.base_agent import BaseAgent
from config.model_routing import pick_model_for_stage
from core import orchestrator


def _stub_openai(*, model, messages, **_kw):
    return {
        "raw": SimpleNamespace(
            choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1))]
        ),
        "text": "{}",
    }


def _make_fetch(resp):
    return lambda cfg, query, agent, task: resp


def _run_once(monkeypatch, caplog, fetch_resp):
    monkeypatch.setattr(ff, "RAG_ENABLED", bool(fetch_resp["rag_snippets"]))
    monkeypatch.setattr(ff, "ENABLE_LIVE_SEARCH", bool(fetch_resp["web_results"]))
    task = {"id": "T1", "role": "Exec", "title": "t", "description": "d"}

    def fake_execute(idea, tasks, agents):
        agent = BaseAgent("Exec", "gpt", "sys", "Task: {task}")
        return {"Exec": agent.run(idea, task)}

    with patch("core.orchestrator.generate_plan", return_value=[task]), patch(
        "core.orchestrator.execute_plan", fake_execute
    ), patch("core.orchestrator.compose_final_proposal", lambda idea, answers: "final"), patch(
        "dr_rd.retrieval.context.fetch_context", _make_fetch(fetch_resp)
    ), patch("core.llm_client.call_openai", _stub_openai), patch(
        "core.agents.base_agent.call_openai", _stub_openai
    ), patch("core.agents.base_agent.fetch_context", _make_fetch(fetch_resp)):
        with caplog.at_level(logging.INFO):
            result = orchestrator.orchestrate("idea")
    return result, caplog.records


def test_e2e_unified_smoke(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_MODE", "legacy")
    m1 = pick_model_for_stage("exec")
    monkeypatch.setenv("DRRD_MODE", "bogus")
    m2 = pick_model_for_stage("exec")
    assert m1 == m2

    rag_resp = {"rag_snippets": ["vec"], "web_results": [], "trace": {"rag_hits": 1, "web_used": False, "backend": "none", "sources": 0, "reason": "ok"}}
    result, records = _run_once(monkeypatch, caplog, rag_resp)
    assert result == "final"
    assert any("UnifiedPipeline:" in r.getMessage() for r in records)
    assert any("RetrievalTrace" in r.getMessage() and "web_used=false" in r.getMessage() for r in records)
    assert not any("TEST_MODE" in r.getMessage() or "mode=" in r.getMessage().lower() for r in records)

    web_resp = {"rag_snippets": [], "web_results": [{"title": "t", "url": "u", "snippet": "s"}], "trace": {"rag_hits": 0, "web_used": True, "backend": "openai", "sources": 1, "reason": "forced"}}
    result, records = _run_once(monkeypatch, caplog, web_resp)
    assert result == "final"
    assert any("RetrievalTrace" in r.getMessage() and "web_used=true" in r.getMessage() for r in records)
