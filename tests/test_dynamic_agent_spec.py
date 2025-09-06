import streamlit as st

from core import orchestrator
from core.orchestrator import execute_plan
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class DummyAgent:
    def __init__(self, model):
        self.model = model

    def run(self, spec):
        # return minimal valid JSON
        return {
            "role": "Dynamic Specialist",
            "task": spec.get("task_brief", ""),
            "summary": "ok",
            "findings": "ok",
            "risks": [],
            "next_steps": [],
            "sources": [],
        }


def test_dynamic_agent_spec_construction(monkeypatch):
    captured = {}

    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        captured.update(task)
        return agent.run(task)

    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)
    st.session_state.clear()
    st.session_state["run_id"] = "r1"
    st.session_state["support_id"] = "s1"
    agents = {"Dynamic Specialist": DummyAgent("m")}
    tasks = [{"id": "T1", "title": "Title", "description": "Desc", "role": "Dynamic Specialist"}]
    execute_plan("idea", tasks, agents=agents, run_id="r")
    assert captured["role_name"] == "Dynamic Specialist"
    assert "task_brief" in captured and captured["task_brief"].startswith("Title")
    assert captured["io_schema_ref"] == "dr_rd/schemas/generic_v2.json"
    assert captured["retrieval_policy"] == RetrievalPolicy.LIGHT
    assert captured["context"]["run_id"] == "r1"
    assert captured["context"]["support_id"] == "s1"
