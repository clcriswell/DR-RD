from types import SimpleNamespace
from unittest.mock import patch

from dr_rd.retrieval.pipeline import ContextBundle
from core.agents.planner_agent import run_planner


def _fake_llm(messages):
    return SimpleNamespace(
        output=[
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="output_text", text="{}")],
            )
        ],
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )
        ],
    )


def test_planner_rag_injection(monkeypatch):
    bundle = ContextBundle(
        rag_snippets=["fact"],
        web_summary=None,
        sources=[],
        meta={"rag_hits": 1, "web_used": False, "backend": "none", "reason": "ok"},
    )
    captured = {}
    with patch("core.agents.planner_agent.collect_context", return_value=bundle), patch(
        "core.agents.planner_agent.llm_call", lambda *a, **k: _fake_llm(captured.setdefault("messages", a[3]))
    ), patch("core.agents.planner_agent.extract_planner_payload", return_value={}):
        run_planner("idea", "model")
    assert "RAG Knowledge" in captured["messages"][1]["content"]


def test_planner_web_injection(monkeypatch):
    bundle = ContextBundle(
        rag_snippets=[],
        web_summary="web",  # type: ignore[arg-type]
        sources=[],
        meta={"rag_hits": 0, "web_used": True, "backend": "openai", "reason": "rag_empty_web_fallback"},
    )
    captured = {}
    with patch("core.agents.planner_agent.collect_context", return_value=bundle), patch(
        "core.agents.planner_agent.llm_call", lambda *a, **k: _fake_llm(captured.setdefault("messages", a[3]))
    ), patch("core.agents.planner_agent.extract_planner_payload", return_value={}):
        run_planner("idea", "model")
    assert "Web Search Results" in captured["messages"][1]["content"]
