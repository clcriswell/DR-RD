import streamlit as st

import core.orchestrator as orch
from core.agents.unified_registry import AGENT_REGISTRY


class DummyAgent:
    def __init__(self, model):
        pass

    def run(self, context, task, model=None):
        return "{}"


def test_routing_fallback_logs_unknown_role(monkeypatch):
    monkeypatch.setitem(AGENT_REGISTRY, "Dynamic Specialist", DummyAgent)
    monkeypatch.setattr(orch, "_invoke_agent", lambda agent, context, task, model=None: "{}")
    st.session_state.clear()
    tasks = [{"id": "T1", "title": "Do", "summary": "something", "role": "Mystery"}]
    orch.execute_plan("idea", tasks, agents={})
    report = st.session_state["routing_report"]
    assert report[0]["routed_role"] == "Dynamic Specialist"
    assert report[0]["unknown_role"] == "Mystery"
