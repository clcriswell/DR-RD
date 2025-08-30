"""Trace page."""
from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.ui.trace_viewer import render_trace
from utils.telemetry import log_event
from utils.paths import artifact_path
from utils.runs import list_runs, last_run_id

runs = list_runs(limit=100)
run_id = st.query_params.get("run_id") or last_run_id()

st.title("Trace")
st.caption("Step-by-step agent activity.")

if runs:
    labels = {
        r["run_id"]: f"{r['run_id']} — {datetime.fromtimestamp(r['started_at']).isoformat()} — {r['idea_preview'][:40]}…"
        for r in runs
    }
    options = list(labels.keys())
    index = options.index(run_id) if run_id in options else 0
    selected = st.selectbox("Run", options, index=index, format_func=lambda x: labels[x])
    if selected != run_id:
        st.query_params["run_id"] = selected
        log_event({"event": "run_selected", "run_id": selected})
        st.rerun()
    run_id = selected
    log_event({"event": "nav_page_view", "page": "trace", "run_id": run_id})
    trace_path = artifact_path(run_id, "trace", "json")
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    else:
        trace = []
    render_trace(trace, run_id=run_id)
else:
    log_event({"event": "nav_page_view", "page": "trace", "run_id": None})
    st.info("No runs found.")
