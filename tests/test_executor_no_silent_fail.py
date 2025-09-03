import pytest
import streamlit as st

from core.orchestrator import execute_plan
from core.agents.unified_registry import AGENT_REGISTRY
from utils import paths, trace_writer


class BoomAgent:
    def __init__(self, model=None):
        pass

    def __call__(self, task):
        raise RuntimeError("boom")


def test_agent_failure_propagates(tmp_path, monkeypatch):
    paths.RUNS_ROOT = tmp_path
    st.session_state.clear()
    run_id = "RUN"
    st.session_state["run_id"] = run_id
    paths.ensure_run_dirs(run_id)
    monkeypatch.setitem(AGENT_REGISTRY, "Boom", BoomAgent)
    tasks = [{"id": "T1", "title": "t", "description": "d", "role": "Boom"}]
    with pytest.raises(RuntimeError):
        execute_plan("idea", tasks, run_id=run_id)
    trace = trace_writer.read_trace(run_id)
    assert any(e.get("event") == "agent_start" for e in trace)
    assert any(e.get("event") == "agent_error" for e in trace)
