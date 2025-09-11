import json
import streamlit as st

from core import orchestrator


def test_no_raw_entities_in_agent_call():
    st.session_state.clear()
    recorded = {}

    class FakeAgent:
        def run(self, context, task, model=None):
            recorded["context"] = context
            recorded["task"] = task
            return "{}"

    task = {"title": "Greet", "description": "Meet Alice Smith at Bob Corp", "context": "Meet Alice Smith at Bob Corp"}
    orchestrator._invoke_agent(FakeAgent(), "irrelevant", task)
    assert "Alice" not in recorded["context"]
    assert task["alias_map"]


def test_alias_map_per_field():
    st.session_state.clear()

    class FakeAgent:
        def run(self, context, task, model=None):
            return "{}"

    t1 = {"title": "T1", "description": "Talk to Alice Smith", "context": "Talk to Alice Smith"}
    t2 = {"title": "T2", "description": "Email Bob Jones", "context": "Email Bob Jones"}
    orchestrator._invoke_agent(FakeAgent(), "i1", t1)
    orchestrator._invoke_agent(FakeAgent(), "i2", t2)
    assert t1["alias_map"] != t2["alias_map"]


def test_synthesis_de_aliases(monkeypatch):
    st.session_state.clear()
    st.session_state["alias_maps"] = {"r": {"Alice": "AliceX1"}}
    monkeypatch.setattr(
        "core.agents.synthesizer_agent.compose_final_proposal",
        lambda *a, **k: json.dumps(
            {
                "summary": "Report about AliceX1",
                "key_points": [],
                "role": "Synthesizer",
                "task": "compose final report",
                "findings": "",
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        ),
    )
    out = orchestrator.compose_final_proposal("Idea about Alice", {"r": "AliceX1 did work"})
    assert "Alice" in out


def test_multi_field_plan(monkeypatch):
    st.session_state.clear()
    calls = []

    class FakeAgent:
        def run(self, context, task, model=None):
            calls.append({"context": context, "task": task})
            return "{}"

    agents = {"Regulatory": FakeAgent(), "Finance": FakeAgent()}
    tasks = [
        {
            "role": "Regulatory",
            "title": "Check",
            "description": "Review Alice filing",
            "context": "Review Alice filing",
        },
        {
            "role": "Finance",
            "title": "Budget",
            "description": "Assess Bob Corp budget",
            "context": "Assess Bob Corp budget",
        },
    ]
    orchestrator.execute_plan(
        "Project about Alice and Bob Corp",
        tasks,
        agents=agents,
        save_decision_log=False,
        save_evidence=False,
    )
    roles = [c["task"]["role"] for c in calls]
    assert "Regulatory" in roles and "Finance" in roles
    reg_call = next(c for c in calls if c["task"]["role"] == "Regulatory")
    fin_call = next(c for c in calls if c["task"]["role"] == "Finance")
    assert "Bob" not in reg_call["context"]
    assert "Alice" not in fin_call["task"]["description"]
    alias_maps = st.session_state.get("alias_maps", {})
    assert set(alias_maps.keys()) == {"Regulatory", "Finance"}
