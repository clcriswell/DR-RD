"""Settings page."""
import json
import copy
from typing import Any
import streamlit as st

from utils.prefs import DEFAULT_PREFS, load_prefs, save_prefs
from utils.telemetry import log_event

if st.query_params.get("view") != "settings":
    st.query_params["view"] = "settings"
log_event({"event": "nav_page_view", "page": "settings"})

st.title("Settings")
st.caption("Configure preferences and defaults.")

prefs = load_prefs()
original = copy.deepcopy(prefs)


def _flatten(d: dict, prefix: str = "", out: dict | None = None) -> dict:
    out = out or {}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _flatten(v, path, out)
        else:
            out[path] = v
    return out

# Defaults for new runs
st.subheader("Defaults for new runs")
mode = st.selectbox(
    "Mode",
    ["standard", "test", "deep"],
    index=["standard", "test", "deep"].index(prefs["defaults"].get("mode", "standard")),
)
max_tokens = st.number_input(
    "Max tokens",
    min_value=0,
    step=100,
    value=prefs["defaults"].get("max_tokens", 0),
)
budget_limit = st.number_input(
    "Budget limit (USD)",
    min_value=0.0,
    step=0.5,
    value=prefs["defaults"].get("budget_limit_usd") or 0.0,
)
knowledge_sources = st.multiselect(
    "Knowledge sources",
    ["samples", "uploads", "connectors"],
    default=prefs["defaults"].get("knowledge_sources", []),
)

# UI behavior
st.subheader("UI behavior")
show_trace = st.checkbox(
    "Show trace by default",
    value=prefs["ui"].get("show_trace_by_default", True),
)
auto_export = st.checkbox(
    "Auto export on completion",
    value=prefs["ui"].get("auto_export_on_completion", False),
)
trace_page_size = st.number_input(
    "Trace page size",
    min_value=10,
    max_value=200,
    value=prefs["ui"].get("trace_page_size", 50),
)

# Privacy
st.subheader("Privacy")
telemetry = st.checkbox(
    "Telemetry enabled",
    value=prefs["privacy"].get("telemetry_enabled", True),
)
share_adv = st.checkbox(
    "Include advanced options in share links",
    value=prefs["privacy"].get("include_advanced_in_share_links", False),
)

updated = {
    "version": DEFAULT_PREFS["version"],
    "defaults": {
        "mode": mode,
        "max_tokens": int(max_tokens),
        "budget_limit_usd": float(budget_limit) if budget_limit else None,
        "knowledge_sources": knowledge_sources,
    },
    "ui": {
        "show_trace_by_default": bool(show_trace),
        "auto_export_on_completion": bool(auto_export),
        "trace_page_size": int(trace_page_size),
    },
    "privacy": {
        "telemetry_enabled": bool(telemetry),
        "include_advanced_in_share_links": bool(share_adv),
    },
}

if st.button("Save preferences", type="primary"):
    save_prefs(updated)
    flat_old = _flatten(original)
    flat_new = _flatten(updated)
    changed = [k for k, v in flat_new.items() if flat_old.get(k) != v]
    log_event({"event": "settings_changed", "keys_changed": changed, "version": updated["version"]})
    st.success("Preferences saved")
    prefs = updated

if st.button("Restore factory defaults"):
    save_prefs(DEFAULT_PREFS)
    log_event({"event": "settings_changed", "keys_changed": list(_flatten(original).keys()), "version": DEFAULT_PREFS["version"]})
    st.success("Preferences restored")
    prefs = load_prefs()

uploaded = st.file_uploader("Import preferences (.json)", type="json")
if uploaded is not None:
    try:
        data = json.load(uploaded)
        save_prefs(data)
        log_event({"event": "settings_imported", "version": data.get("version")})
        st.success("Preferences imported")
        prefs = load_prefs()
    except Exception:
        st.error("Invalid preferences file")

if st.download_button(
    "Export preferences",
    data=json.dumps(prefs).encode("utf-8"),
    file_name="config.json",
):
    log_event({"event": "settings_exported", "version": prefs.get("version")})
