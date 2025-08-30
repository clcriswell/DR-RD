"""Metrics page."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from utils import metrics
from utils.telemetry import log_event
from app.ui import empty_states
from utils.i18n import tr as t
from app.ui.command_palette import open_palette

# quick open via button
if st.button(
    "⌘K Command palette",
    key="cmd_btn",
    use_container_width=False,
    help="Open global search",
):
    log_event({"event": "palette_opened"})
    open_palette()

# auto open via query param
if st.query_params.get("cmd") == "1":
    log_event({"event": "palette_opened", "source": "qp"})
    open_palette()
    st.query_params.pop("cmd", None)

act = st.session_state.pop("_cmd_action", None)
if act:
    if act["action"] == "switch_page":
        st.switch_page(act["params"]["page"])
    elif act["action"] == "set_params":
        st.query_params.update(act["params"])
        st.rerun()
    elif act["action"] == "copy":
        st.code(act["params"]["text"], language=None)
        st.toast("Copied link")
    elif act["action"] == "start_demo":
        st.query_params.update({"mode": "demo", "view": "run"})
        st.toast("Demo mode selected. Review and start.")
    log_event(
        {
            "event": "palette_executed",
            "kind": act.get("kind"),
            "action": act["action"],
        }
    )

if st.query_params.get("view") != "metrics":
    st.query_params["view"] = "metrics"
log_event({"event": "nav_page_view", "page": "metrics"})

st.title(t("metrics_title"))
st.caption(t("metrics_caption"))

start_default = date.today() - timedelta(days=7)
start, end = st.date_input(t("date_range_label"), value=(start_default, date.today()), help=t("metrics_date_help"))
start_ts = datetime.combine(start, datetime.min.time()).timestamp()
end_ts = datetime.combine(end, datetime.max.time()).timestamp()

events = [e for e in metrics.load_events() if start_ts <= e.get("ts", 0) <= end_ts]
surveys = [s for s in metrics.load_surveys() if start_ts <= s.get("ts", 0) <= end_ts]
if not events and not surveys:
    empty_states.metrics_empty()
else:
    agg = metrics.compute_aggregates(events, surveys)

    col1, col2, col3 = st.columns(3)
    col1.metric("Runs", agg["runs"])
    col2.metric("Page views", agg["views"])
    col3.metric("Errors", agg["errors"])

    st.subheader("Run Quality")
    st.table(
        [
            {
                "error_rate": agg["error_rate"],
                "success_rate": agg["success_rate"],
                "avg_time_on_task": agg["avg_time_on_task"],
            }
        ]
    )

    st.subheader("Surveys")
    if surveys:
        st.table(
            [
                {
                    "sus_count": agg["sus_count"],
                    "sus_mean": agg["sus_mean"],
                    "sus_7_day_mean": agg["sus_7_day_mean"],
                    "seq_count": agg["seq_count"],
                    "seq_mean": agg["seq_mean"],
                    "seq_7_day_mean": agg["seq_7_day_mean"],
                }
            ]
        )
