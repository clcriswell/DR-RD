import json

import streamlit as st

from core.orchestrator import execute_plan


class DummyAgent:
    def __init__(self, model: str | None = None):
        pass

    def run(self, idea: str, task: dict, model: str | None = None) -> str:
        payload = {
            "role": task.get("role", ""),
            "task": task.get("title", ""),
            "findings": "done",
            "risks": [],
            "next_steps": [],
            "sources": [],
            "tokens_in": 1,
            "tokens_out": 2,
            "cost": 0.0031,
            "quotes": ["evidence"],
            "citations": [],
        }
        return "```json\n" + json.dumps(payload) + "\n```"


def test_trace_capture(monkeypatch):
    st.session_state.clear()

    def fake_choose(role, title, desc, summary=None, ui_model=None, task=None):
        return role or "CTO", DummyAgent, "gpt-4o-mini"

    monkeypatch.setattr("core.router.choose_agent_for_task", fake_choose)

    tasks = [{"id": "T01", "role": "CTO", "title": "Test", "description": "do"}]
    execute_plan("idea", tasks, agents={})

    trace = st.session_state.get("agent_trace")
    assert trace and trace[0]["role"] == "CTO"
    assert trace[0]["model"] == "gpt-4o-mini"
    assert trace[0]["tokens_in"] == 1
    assert trace[0]["events"][0]["type"] == "route"
