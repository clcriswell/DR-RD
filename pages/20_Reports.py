"""Reports and exports page."""
import streamlit as st

from utils import trace_export
from utils.telemetry import log_event
from app import generate_pdf

log_event({"event": "nav_page_view", "page": "reports"})

st.title("Reports & Exports")
st.caption("Download outputs from your last run.")

report = st.session_state.get("run_report")
trace = st.session_state.get("agent_trace", [])
run_id = st.session_state.get("run_id")

if not report and not trace:
    st.info("No run data found.")
else:
    if report:
        st.subheader("Report")
        col_md, col_pdf = st.columns(2)
        if col_md.download_button(
            "Download report (.md)",
            data=report.encode("utf-8"),
            file_name=f"report_{run_id or 'session'}.md",
            mime="text/markdown",
            use_container_width=True,
        ):
            log_event({"event": "export_clicked", "format": "report_md", "run_id": run_id})
        if col_pdf.download_button(
            "Download report (.pdf)",
            data=generate_pdf(report),
            file_name=f"report_{run_id or 'session'}.pdf",
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
            file_name=f"trace_{run_id or 'session'}.json",
            mime="application/json",
            use_container_width=True,
        ):
            log_event({"event": "export_clicked", "format": "trace_json", "run_id": run_id})
        if col_csv.download_button(
            "Download trace (.csv)",
            data=trace_export.to_csv(trace, run_id=run_id),
            file_name=f"trace_{run_id or 'session'}.csv",
            mime="text/csv",
            use_container_width=True,
        ):
            log_event({"event": "export_clicked", "format": "trace_csv", "run_id": run_id})
