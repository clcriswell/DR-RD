import streamlit as st

from app.agent_trace_ui import (
    render_live_status,
    render_role_summaries,
)
from app.ui.trace_viewer import render_trace


def test_agent_trace_ui_smoke(tmp_path):
    st.session_state.clear()
    live_status = {
        "T01": {
            "done": True,
            "progress": 1.0,
            "tokens_in": 1,
            "tokens_out": 2,
            "cost_usd": 0.1,
            "model": "gpt",
            "role": "CTO",
            "title": "Test",
        }
    }
    trace = [
        {
            "phase": "planner",
            "name": "Plan",
            "status": "complete",
            "started_at": 0,
            "ended_at": 1,
            "duration_ms": 1000,
            "tokens": 1,
            "cost": 0.1,
            "summary": "done",
            "raw": {},
            "step_id": "s1",
        }
    ]
    render_live_status(live_status)
    render_trace(trace, run_id="proj")
    render_role_summaries({"CTO": "output"})
