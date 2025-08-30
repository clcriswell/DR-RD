"""Trace page."""
import streamlit as st

from app.ui.trace_viewer import render_trace
from utils.telemetry import log_event

run_id = st.query_params.get("run_id")
log_event({"event": "nav_page_view", "page": "trace", "run_id": run_id})

st.title("Trace")
st.caption("Step-by-step agent activity.")

trace = st.session_state.get("agent_trace", [])
render_trace(trace, run_id=run_id or st.session_state.get("run_id") or "last")
