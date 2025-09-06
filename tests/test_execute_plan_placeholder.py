import json
import streamlit as st
from core import orchestrator
from core.orchestrator import execute_plan

class BadAgent:
    def __init__(self, model):
        self.model = model
    def run(self, spec):
        return {}

def test_placeholder_open_issue(monkeypatch):
    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        return {}
    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)
    st.session_state.clear()
    agents = {"CTO": BadAgent("m")}
    tasks = [{"id": "T1", "title": "A", "description": "B", "role": "CTO"}]
    execute_plan("idea", tasks, agents=agents, run_id="r1")
    assert st.session_state.get("open_issues")


def test_missing_fields_placeholder(monkeypatch):
    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        raise ValueError("Missing required fields in PromptAgent inputs: task")

    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)
    st.session_state.clear()
    agents = {"CTO": object()}
    tasks = [{"id": "T1", "title": "A", "description": "B", "role": "CTO"}]
    answers = execute_plan("idea", tasks, agents=agents, run_id="r1")
    out = json.loads(answers["CTO"][0])
    assert out["summary"] == "Not determined"
    assert out["task"] == "A"
