"""Metrics page."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from app.ui import empty_states
from app.ui.a11y import aria_live_region, inject, main_start
from app.ui.command_palette import open_palette
from utils import metrics
from utils.i18n import tr as t
from utils.telemetry import log_event

inject()
main_start()
metrics_region = aria_live_region("metrics")

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
date_range = st.date_input(
    t("date_range_label"), value=(start_default, date.today()), help=t("metrics_date_help")
)
if isinstance(date_range, (list, tuple)):
    if len(date_range) == 2:
        start, end = date_range
    elif len(date_range) == 1:
        start = end = date_range[0]
    else:
        start = end = start_default
else:
    start = end = date_range
start_ts = datetime.combine(start, datetime.min.time()).timestamp()
end_ts = datetime.combine(end, datetime.max.time()).timestamp()

events = [e for e in metrics.load_events() if start_ts <= e.get("ts", 0) <= end_ts]
surveys = [s for s in metrics.load_surveys() if start_ts <= s.get("ts", 0) <= end_ts]
if not events and not surveys:
    empty_states.metrics_empty()
else:
    agg = metrics.compute_aggregates(events, surveys)
    cost = sum(e.get("cost_usd", 0.0) for e in events)
    st.markdown(
        f"<script>document.getElementById('{metrics_region}').innerText = 'Metrics loaded';</script>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Runs", agg["runs"])
    col2.metric("Page views", agg["views"])
    col3.metric("Errors", agg["errors"])
    col4.metric(label="Total cost (USD)", value=f"${cost:.2f}")

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
