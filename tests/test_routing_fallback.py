import streamlit as st

import core.orchestrator as orch
from core.agents.unified_registry import AGENT_REGISTRY
from core.router import route_task


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
    assert report[0]["planned_role"] == "Mystery"


def test_keyword_from_summary():
    st.session_state.clear()
    task = {"id": "T1", "title": "Budget", "summary": "Plan budget", "role": None}
    role, cls, model, routed = route_task(task)
    assert role == "Finance"


def test_keyword_from_description():
    st.session_state.clear()
    task = {"id": "T1", "title": "Budget", "description": "Plan budget", "role": None}
    role, cls, model, routed = route_task(task)
    assert role == "Finance"


def test_unknown_role_falls_back():
    st.session_state.clear()
    task = {"id": "T1", "title": "Do", "summary": "stuff", "role": "Mystery"}
    role, cls, model, routed = route_task(task)
    assert role == "Dynamic Specialist"
