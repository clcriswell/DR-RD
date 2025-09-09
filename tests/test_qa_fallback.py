import json
import streamlit as st

from core.agents.qa_agent import QAAgent
from core.agents.reflection_agent import ReflectionAgent
import core.orchestrator as orchestrator
import config.feature_flags as ff


def test_qa_retry_on_placeholders(monkeypatch):
    st.session_state.clear()
    calls = {"qa": 0}

    def fake_run(self, *args, **kwargs):
        calls["qa"] += 1
        if calls["qa"] == 1:
            return {
                "role": "QA",
                "task": "t",
                "summary": "",
                "findings": "",
                "defects": [],
                "coverage": "",
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        return {
            "role": "QA",
            "task": "t",
            "summary": "done",
            "findings": "",
            "defects": [],
            "coverage": "",
            "risks": [],
            "next_steps": [],
            "sources": [],
        }

    monkeypatch.setattr(QAAgent, "run", fake_run)
    monkeypatch.setattr(
        orchestrator, "route_task", lambda task, ui_model=None: ("QA", QAAgent, "m", task)
    )
    monkeypatch.setattr(
        orchestrator,
        "validate_and_retry",
        lambda role, routed, text, retry_fn, run_id=None, support_id=None: (text, {"valid_json": True, "retried": False}),
    )
    answers = orchestrator.execute_plan(
        "idea", [{"role": "QA", "title": "t", "description": "d"}], agents={}, ui_model=None, save_evidence=False, save_decision_log=False
    )
    assert calls["qa"] == 2
    data = json.loads(answers["QA"])
    assert data["summary"] == "done"


def test_post_qa_reflection_followup(monkeypatch):
    st.session_state.clear()
    calls = {"qa": 0, "reflection": 0}

    def qa_run(self, *args, **kwargs):
        calls["qa"] += 1
        return {
            "role": "QA",
            "task": "t",
            "summary": "",
            "findings": "",
            "defects": [],
            "coverage": "",
            "risks": [],
            "next_steps": [],
            "sources": [],
        }

    monkeypatch.setattr(QAAgent, "run", qa_run)

    def reflection_run(self, *args, **kwargs):
        calls["reflection"] += 1
        return '["[Finance]: review"]'

    monkeypatch.setattr(ReflectionAgent, "run", reflection_run)

    class DummyFinance:
        def __init__(self, model):
            pass

        def run(self, task):
            return json.dumps(
                {
                    "role": "Finance",
                    "task": task.get("title"),
                    "summary": "ok",
                    "findings": "x",
                    "defects": [],
                    "coverage": "",
                    "risks": [],
                    "next_steps": [],
                    "sources": [],
                }
            )

    def fake_route(task, ui_model=None):
        if task.get("role") == "QA":
            return ("QA", QAAgent, "m1", task)
        return (task.get("role"), DummyFinance, "m2", task)

    monkeypatch.setattr(orchestrator, "route_task", fake_route)
    monkeypatch.setattr(
        orchestrator,
        "invoke_agent_safely",
        lambda agent, task, model=None, meta=None, run_id=None: agent.run(task),
    )
    monkeypatch.setattr(
        orchestrator,
        "validate_and_retry",
        lambda role, routed, text, retry_fn, run_id=None, support_id=None: (text, {"valid_json": True, "retried": False}),
    )
    monkeypatch.setattr(ff, "EVALUATION_ENABLED", False)
    monkeypatch.setattr(ff, "REFLECTION_ENABLED", True)

    orchestrator.execute_plan(
        "idea", [{"role": "QA", "title": "t", "description": "d"}], agents={}, ui_model=None, save_evidence=False, save_decision_log=False
    )
    assert calls["qa"] == 2
    assert calls["reflection"] == 1
