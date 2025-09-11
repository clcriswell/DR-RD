from types import SimpleNamespace

import config.feature_flags as ff
from core import orchestrator


def test_full_pipeline_smoke(monkeypatch):
    # Disable retrieval and live search for deterministic test
    monkeypatch.setattr(ff, "RAG_ENABLED", False)
    monkeypatch.setattr(ff, "ENABLE_LIVE_SEARCH", False)

    # Minimal streamlit stub
    monkeypatch.setattr(orchestrator, "st", SimpleNamespace(session_state={}))

    # Stub retrieval context to avoid external calls
    ctx = {"rag_snippets": [], "web_results": [], "trace": {"rag_hits": 0, "web_used": False, "backend": "none", "sources": 0, "reason": "stub"}}
    monkeypatch.setattr("dr_rd.retrieval.context.fetch_context", lambda *a, **k: ctx)
    monkeypatch.setattr("core.agents.base_agent.fetch_context", lambda *a, **k: ctx)

    # Deterministic LLM responses keyed by system prompt
    def fake_call_openai(*, messages, **_kwargs):
        system_msg = messages[0]["content"] if messages else ""
        if "Planner" in system_msg:
            text = '{"tasks":[{"id":"T1","title":"Research","summary":"Do research","description":"desc","role":"Research Scientist"}]}'
        elif "Research Scientist" in system_msg:
            text = '{"summary":"Research complete","findings":"","gaps":"","risks":[],"next_steps":[],"sources":[],"role":"Research Scientist","task":"T1"}'
        else:
            text = '### Research Scientist\nResearch complete'
        raw = SimpleNamespace(choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0))])
        return {"raw": raw, "text": text}

    monkeypatch.setattr("core.llm_client.call_openai", fake_call_openai)
    monkeypatch.setattr("core.llm.call_openai", fake_call_openai)
    monkeypatch.setattr("core.agents.base_agent.call_openai", fake_call_openai)

    result = orchestrator.orchestrate("Build a rocket")
    assert "Research complete" in result
