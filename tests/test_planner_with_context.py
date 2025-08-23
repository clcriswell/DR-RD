from types import SimpleNamespace
from unittest.mock import patch

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
    ctx = {
        "rag_snippets": ["fact"],
        "web_results": [],
        "trace": {
            "rag_hits": 1,
            "web_used": False,
            "backend": "none",
            "sources": 0,
            "reason": "ok",
        },
    }
    captured = {}
    with patch("core.agents.planner_agent.fetch_context", return_value=ctx), patch(
        "core.agents.planner_agent.llm_call",
        lambda *a, **k: _fake_llm(captured.setdefault("messages", a[3])),
    ), patch("core.agents.planner_agent.extract_planner_payload", return_value={}):
        run_planner("idea", "model")
    assert "RAG Knowledge" in captured["messages"][1]["content"]


def test_planner_web_injection(monkeypatch):
    ctx = {
        "rag_snippets": [],
        "web_results": [{"title": "t", "url": "u", "snippet": "s"}],
        "trace": {
            "rag_hits": 0,
            "web_used": True,
            "backend": "openai",
            "sources": 1,
            "reason": "rag_zero_hits",
        },
    }
    captured = {}
    with patch("core.agents.planner_agent.fetch_context", return_value=ctx), patch(
        "core.agents.planner_agent.llm_call",
        lambda *a, **k: _fake_llm(captured.setdefault("messages", a[3])),
    ), patch("core.agents.planner_agent.extract_planner_payload", return_value={}):
        run_planner("idea", "model")
    assert "Web Search Results" in captured["messages"][1]["content"]
