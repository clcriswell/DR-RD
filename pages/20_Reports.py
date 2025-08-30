"""Reports and exports page."""
from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from utils import trace_export
from utils.telemetry import log_event
from utils.paths import artifact_path
from utils.runs import list_runs, last_run_id
from app import generate_pdf

runs = list_runs(limit=100)
run_id = st.query_params.get("run_id") or last_run_id()

st.title("Reports & Exports")
st.caption("Download outputs from your last run.")

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
    log_event({"event": "nav_page_view", "page": "reports", "run_id": run_id})
    report_path = artifact_path(run_id, "report", "md")
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else None
    trace_path = artifact_path(run_id, "trace", "json")
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.exists() else []
    if not report and not trace:
        st.info("No run data found.")
    else:
        if report:
            st.subheader("Report")
            col_md, col_pdf = st.columns(2)
            if col_md.download_button(
                "Download report (.md)",
                data=report.encode("utf-8"),
                file_name=artifact_path(run_id, "report", "md").name,
                mime="text/markdown",
                use_container_width=True,
            ):
                log_event({"event": "export_clicked", "format": "report_md", "run_id": run_id})
            if col_pdf.download_button(
                "Download report (.pdf)",
                data=generate_pdf(report),
                file_name=artifact_path(run_id, "report", "pdf").name,
                mime="application/pdf",
                use_container_width=True,
            ):
                log_event({"event": "export_clicked", "format": "report_pdf", "run_id": run_id})
        if trace:
            st.subheader("Trace")
            col_json, col_csv = st.columns(2)
            if col_json.download_button(
                "Download trace (.json)",
                data=trace_export.to_json(trace),
                file_name=artifact_path(run_id, "trace", "json").name,
                mime="application/json",
                use_container_width=True,
            ):
                log_event({"event": "export_clicked", "format": "trace_json", "run_id": run_id})
            if col_csv.download_button(
                "Download summary (.csv)",
                data=trace_export.to_csv(trace, run_id=run_id),
                file_name=artifact_path(run_id, "summary", "csv").name,
                mime="text/csv",
                use_container_width=True,
            ):
                log_event({"event": "export_clicked", "format": "trace_csv", "run_id": run_id})
else:
    log_event({"event": "nav_page_view", "page": "reports", "run_id": None})
    st.info("No runs found.")
