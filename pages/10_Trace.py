"""Trace page."""
from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode

import streamlit as st

from app.ui.trace_viewer import render_trace
from utils.telemetry import log_event
from utils.paths import artifact_path
from utils.runs import list_runs, last_run_id
from utils.query_params import view_state_from_params, encode_config
from utils.run_config import from_session, to_orchestrator_kwargs

state = view_state_from_params(st.query_params)
runs = list_runs(limit=100)
run_id = state["run_id"] or last_run_id()
if st.query_params.get("view") != "trace":
    st.query_params["view"] = "trace"

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
    include_adv = st.checkbox("Include advanced options", key="trace_share_adv")
    if st.button("Copy shareable link", key="trace_share"):
        cfg_dict = to_orchestrator_kwargs(from_session())
        if not include_adv:
            cfg_dict.pop("advanced", None)
        qp = encode_config(cfg_dict)
        qp.update({"view": "trace", "run_id": run_id})
        if tv := st.query_params.get("trace_view"):
            qp["trace_view"] = tv
        if q := st.query_params.get("q"):
            qp["q"] = q
        url = "./?" + urlencode(qp)
        st.text_input("trace_share_url", value=url, label_visibility="collapsed")
        log_event(
            {
                "event": "link_shared",
                "where": "trace",
                "included_adv": bool(include_adv),
            }
        )
    render_trace(
        trace,
        run_id=run_id,
        default_view=state["trace_view"],
        default_query=state["trace_query"],
    )
else:
    log_event({"event": "nav_page_view", "page": "trace", "run_id": None})
    st.info("No runs found.")
