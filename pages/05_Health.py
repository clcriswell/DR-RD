from __future__ import annotations

import os

import streamlit as st

from app.ui.command_palette import open_palette
from utils import health_check
from utils.i18n import tr as t
from utils.lazy_import import local_import
from utils.telemetry import log_event

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

st.title(t("health_title"))

if st.button("Run diagnostics"):
    report = health_check.run_all()
    cols = st.columns(3)
    cols[0].metric("pass", report.summary.get("pass", 0))
    cols[1].metric("warn", report.summary.get("warn", 0))
    cols[2].metric("fail", report.summary.get("fail", 0))
    pd = local_import("pandas")
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
