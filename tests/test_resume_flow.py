import json

import streamlit as st

from utils import checkpoints, telemetry, paths
from utils import trace_writer
from core import orchestrator


def test_resume_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    checkpoints.ROOT = tmp_path
    events = []
    monkeypatch.setattr(telemetry, "log_event", lambda ev: events.append(ev))

    # Create run A with planner completed
    paths.RUNS_ROOT = tmp_path
    checkpoints.ROOT = tmp_path
    checkpoints.init("A", phases=["planner", "executor", "synth"])
    checkpoints.mark_step_done("A", "planner", "plan")
    # create prior trace with tasks
    trace_writer.append_step(
        "A",
        {
            "phase": "planner",
            "step": "plan",
            "summary": [
                {"id": "T1", "role": "Exec", "title": "t", "description": "d"}
            ],
        },
    )

    called = {"planner": 0, "executor": 0, "synth": 0}

    def fake_generate(idea):
        called["planner"] += 1
        return []

    def fake_execute(idea, tasks, agents):
        called["executor"] += 1
        assert tasks == [{"id": "T1", "role": "Exec", "title": "t", "description": "d"}]
        return {}

    def fake_synth(idea, results):
        called["synth"] += 1
        return "final"

    monkeypatch.setattr(orchestrator, "generate_plan", fake_generate)
    monkeypatch.setattr(orchestrator, "execute_plan", fake_execute)
    monkeypatch.setattr(orchestrator, "compose_final_proposal", fake_synth)

    st.session_state["run_id"] = "B"
    out = orchestrator.orchestrate("idea", resume_from="A")
    assert out == "final"
    assert called["planner"] == 0  # skipped
    assert called["executor"] == 1
    assert called["synth"] == 1
    assert any(ev["event"] == "run_resumed" for ev in events)
