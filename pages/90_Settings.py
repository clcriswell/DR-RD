"""Settings page."""
import streamlit as st

from utils.run_config import defaults
from utils.telemetry import log_event
from app import load_ui_config, save_ui_config

if st.query_params.get("view") != "settings":
    st.query_params["view"] = "settings"
log_event({"event": "nav_page_view", "page": "settings"})

st.title("Settings")
st.caption("Configure default run options.")

stored = load_ui_config()
base = defaults()

mode = st.selectbox(
    "Default mode",
    ["standard", "test", "deep"],
    index=["standard", "test", "deep"].index(stored.get("mode", base.mode)),
)
auto_trace = st.checkbox(
    "Auto export trace",
    value=stored.get("auto_export_trace", base.auto_export_trace),
)
auto_report = st.checkbox(
    "Auto export report",
    value=stored.get("auto_export_report", base.auto_export_report),
)

if st.button("Save", type="primary", use_container_width=True):
    data = {
        "mode": mode,
        "auto_export_trace": auto_trace,
        "auto_export_report": auto_report,
    }
    save_ui_config(data)
    for k, v in data.items():
        st.session_state[k] = v
    log_event({"event": "settings_changed", **data})
    st.success("Settings saved")
