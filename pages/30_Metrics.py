"""Metrics page."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from utils import metrics
from utils.telemetry import log_event

if st.query_params.get("view") != "metrics":
    st.query_params["view"] = "metrics"
log_event({"event": "nav_page_view", "page": "metrics"})

st.title("Metrics")
st.caption("Local usage and survey metrics.")

start_default = date.today() - timedelta(days=7)
start, end = st.date_input("Date range", value=(start_default, date.today()))
start_ts = datetime.combine(start, datetime.min.time()).timestamp()
end_ts = datetime.combine(end, datetime.max.time()).timestamp()

events = [e for e in metrics.load_events() if start_ts <= e.get("ts", 0) <= end_ts]
surveys = [s for s in metrics.load_surveys() if start_ts <= s.get("ts", 0) <= end_ts]
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
else:
    st.info("No survey data in range.")
