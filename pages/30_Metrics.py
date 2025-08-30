"""Metrics page."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from utils import survey_store
from utils.telemetry import log_event

log_event({"event": "nav_page_view", "page": "metrics"})

st.title("Metrics")
st.caption("Local usage and survey metrics.")

start_default = date.today() - timedelta(days=7)
start, end = st.date_input("Date range", value=(start_default, date.today()))
start_ts = datetime.combine(start, datetime.min.time()).timestamp()
end_ts = datetime.combine(end, datetime.max.time()).timestamp()

# Load telemetry events
events_path = Path(".dr_rd/telemetry/events.jsonl")
events = []
if events_path.exists():
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            ev = json.loads(line)
            ts = ev.get("ts", 0)
            if start_ts <= ts <= end_ts:
                events.append(ev)

runs = sum(1 for e in events if e.get("event") == "start_run")
views = sum(1 for e in events if e.get("event") == "nav_page_view")
errors = sum(1 for e in events if e.get("event") == "error_shown")

col1, col2, col3 = st.columns(3)
col1.metric("Runs", runs)
col2.metric("Page views", views)
col3.metric("Errors", errors)

records = survey_store.load_recent(1000)
records = [r for r in records if start_ts <= r.get("ts", 0) <= end_ts]
agg = survey_store.compute_aggregates(records)

st.subheader("Surveys")
if records:
    st.table(agg)
else:
    st.info("No survey data in range.")
