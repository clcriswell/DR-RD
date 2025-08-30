from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from utils import health_check
from utils.telemetry import log_event

st.title("System Health")

if st.button("Run diagnostics"):
    report = health_check.run_all()
    cols = st.columns(3)
    cols[0].metric("pass", report.summary.get("pass", 0))
    cols[1].metric("warn", report.summary.get("warn", 0))
    cols[2].metric("fail", report.summary.get("fail", 0))
    df = pd.DataFrame([{"id": c.id, "name": c.name, "status": c.status} for c in report.checks])
    st.dataframe(df, use_container_width=True)
    for c in report.checks:
        with st.expander(c.name):
            st.write(c.details)
            if c.remedy:
                st.caption(c.remedy)
    st.download_button(
        "health_report.json",
        data=health_check.to_json(report),
        file_name="health_report.json",
        mime="application/json",
    )
    st.download_button(
        "health_report.md",
        data=health_check.to_markdown(report),
        file_name="health_report.md",
        mime="text/markdown",
    )
    log_event({"event": "health_check_run", "summary": report.summary})
    if os.getenv("NO_NET") == "1":
        st.caption("Network tests skipped")
else:
    st.write("Click to run diagnostics")
