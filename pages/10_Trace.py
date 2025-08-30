"""Trace page."""

from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode

import streamlit as st

from app.ui import empty_states
from app.ui.copy import t
from app.ui.trace_viewer import render_trace
from utils import run_reproduce
from utils.paths import artifact_path
from utils.query_params import encode_config, view_state_from_params
from utils.run_config import from_session, to_orchestrator_kwargs
from utils.runs import last_run_id, list_runs
from utils.telemetry import log_event
from utils.flags import is_enabled

params = dict(st.query_params)
state = view_state_from_params(params)
runs = list_runs(limit=100)
run_id = state["run_id"] or last_run_id()
if params.get("view") != "trace":
    st.query_params["view"] = "trace"

st.title(t("trace_title"))
st.caption(t("trace_caption"))

if runs:
    labels = {
        r[
            "run_id"
        ]: f"{r['run_id']} — {datetime.fromtimestamp(r['started_at']).isoformat()} — {r['idea_preview'][:40]}…"
        for r in runs
    }
    options = list(labels.keys())
    index = options.index(run_id) if run_id in options else 0
    selected = st.selectbox(
        t("run_label"),
        options,
        index=index,
        format_func=lambda x: labels[x],
        help=t("run_select_help"),
    )
    if selected != run_id:
        st.query_params["run_id"] = selected
        log_event({"event": "run_selected", "run_id": selected})
        st.rerun()
    run_id = selected
    meta = next((r for r in runs if r["run_id"] == run_id), {})
    log_event({"event": "nav_page_view", "page": "trace", "run_id": run_id})
    trace_path = artifact_path(run_id, "trace", "json")
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    else:
        trace = []
    if not trace:
        empty_states.trace_empty()
    else:
        if meta.get("status") == "resumable":
            st.info("This run can be resumed.")
            if st.button("Resume run", use_container_width=True):
                st.query_params.update({"resume_from": run_id, "view": "run"})
                st.switch_page("app.py")
        include_adv = st.checkbox(
            t("include_adv_label"), key="trace_share_adv", help=t("include_adv_help")
        )
        if st.button(t("share_link_label"), key="trace_share", help=t("share_link_help")):
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
            st.text_input(t("share_link_url_label"), value=url, help=t("share_link_help"))
            log_event(
                {
                    "event": "link_shared",
                    "where": "trace",
                    "included_adv": bool(include_adv),
                }
            )
        if st.button("Reproduce run", use_container_width=True):
            try:
                locked = run_reproduce.load_run_inputs(run_id)
                kwargs = run_reproduce.to_orchestrator_kwargs(locked)
                st.query_params.update(
                    encode_config(kwargs) | {"view": "run", "origin_run_id": run_id}
                )
                st.toast("Prefilled from saved config. Review and start the run.")
                log_event({"event": "reproduce_prep", "run_id": run_id})
            except FileNotFoundError:
                st.toast("Missing run lockfile", icon="⚠️")
        if is_enabled("trace_viewer_v2", params=params):
            render_trace(
                trace,
                run_id=run_id,
                default_view=state["trace_view"],
                default_query=state["trace_query"],
            )
        else:
            render_trace(
                trace,
                run_id=run_id,
                default_view=state["trace_view"],
                default_query=state["trace_query"],
            )
else:
    log_event({"event": "nav_page_view", "page": "trace", "run_id": None})
    empty_states.trace_empty()
