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

    # Use generic prompt for Synthesizer to avoid template requirements
    from dr_rd.prompting import prompt_registry

    orig_get = prompt_registry.registry.get

    def fake_get(role, task_key=None):
        if role == "Synthesizer":
            return None
        return orig_get(role, task_key)

    monkeypatch.setattr(prompt_registry.registry, "get", fake_get)

    # Deterministic LLM responses keyed by system prompt
    def fake_call_openai(*, messages, **_kwargs):
        system_msg = messages[0]["content"] if messages else ""
        if "Planner" in system_msg:
            text = (
                '{"tasks":[{"id":"T1","title":"Research","summary":"Do research",'
                '"description":"desc","role":"Research Scientist"}]}'
            )
        elif "Research Scientist" in system_msg:
            text = (
                '{"summary":"Research complete","findings":"All good","gaps":"",'
                '"risks":["Risk"],"next_steps":["Step"],"sources":[{"url":'
                '"http://example.com"}],"role":"Research Scientist","task":"T1"}'
            )
        elif "Synthesizer" in system_msg:
            text = (
                '{"summary":"Overall summary","key_points":["KP"],'
                '"findings":"Combined findings","risks":["Synth risk"],'
                '"next_steps":["Synth step"],"sources":[{"url":"http://example.com"}]}'
            )
        else:
            text = "{}"
        raw = SimpleNamespace(
            choices=[SimpleNamespace(usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0))]
        )
        return {"raw": raw, "text": text}

    monkeypatch.setattr("core.llm_client.call_openai", fake_call_openai)
    monkeypatch.setattr("core.llm.call_openai", fake_call_openai)
    monkeypatch.setattr("core.agents.base_agent.call_openai", fake_call_openai)

    result = orchestrator.orchestrate("Build a rocket")
    assert "## Summary" in result
    assert "Overall summary" in result
    assert "## Key Points" in result
    assert "KP" in result
    assert "## Findings" in result
    assert "Combined findings" in result
    assert "## Risks" in result
    assert "Synth risk" in result
    assert "## Next Steps" in result
    assert "Synth step" in result
    assert "## Sources" in result
    assert "http://example.com" in result
    assert "Not determined" not in result
    assert "TODO" not in result
