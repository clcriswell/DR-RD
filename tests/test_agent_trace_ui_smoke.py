import streamlit as st

from app.agent_trace_ui import (
    render_agent_trace,
    render_live_status,
    render_role_summaries,
    render_exports,
)


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
            "project_id": "p",
            "task_id": "T01",
            "step_no": 1,
            "role": "CTO",
            "title": "Test",
            "model": "gpt",
            "tokens_in": 1,
            "tokens_out": 2,
            "cost_usd": 0.1,
            "quotes": [],
            "citations": [],
            "finding": "done",
            "raw_json": {},
            "events": [],
            "ts_start": "",
            "ts_end": "",
        }
    ]
    render_live_status(live_status)
    render_agent_trace(trace, {})
    render_role_summaries({"CTO": "output"})
    render_exports("proj", trace)
