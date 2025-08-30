"""Settings page."""

import copy
import json

import streamlit as st

from app.ui.command_palette import open_palette
from utils.i18n import get_locale, set_locale
from utils.i18n import tr as t
from utils.prefs import DEFAULT_PREFS, load_prefs, save_prefs
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

if st.query_params.get("view") != "settings":
    st.query_params["view"] = "settings"
log_event({"event": "nav_page_view", "page": "settings"})

prefs = load_prefs()
lang = st.selectbox(
    "Language",
    ["en", "es"],
    index=["en", "es"].index(get_locale()),
    help="UI language",
)
if st.button("Apply language"):
    set_locale(lang)
    prefs["ui"]["language"] = lang
    save_prefs(prefs)
    log_event({"event": "locale_changed", "lang": lang})
    st.rerun()

st.title(t("settings_title"))
st.caption(t("settings_help"))

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
    t("mode_label"),
    ["standard", "test", "deep"],
    index=["standard", "test", "deep"].index(prefs["defaults"].get("mode", "standard")),
    help=t("mode_help"),
)
max_tokens = st.number_input(
    t("max_tokens_label"),
    min_value=0,
    step=100,
    value=prefs["defaults"].get("max_tokens") or 0,
    help=t("max_tokens_help"),
)
budget_limit = st.number_input(
    t("budget_limit_label"),
    min_value=0.0,
    step=0.5,
    value=prefs["defaults"].get("budget_limit_usd") or 0.0,
    help=t("budget_limit_help"),
)
knowledge_sources = st.multiselect(
    t("knowledge_sources_label"),
    ["samples", "uploads", "connectors"],
    default=prefs["defaults"].get("knowledge_sources", []),
    help=t("knowledge_sources_help"),
)

# UI behavior
st.subheader("UI behavior")
show_trace = st.checkbox(
    t("show_trace_label"),
    value=prefs["ui"].get("show_trace_by_default", True),
    help=t("show_trace_help"),
)
auto_export = st.checkbox(
    t("auto_export_label"),
    value=prefs["ui"].get("auto_export_on_completion", False),
    help=t("auto_export_help"),
)
trace_page_size = st.number_input(
    t("trace_page_size_label"),
    min_value=10,
    max_value=200,
    value=prefs["ui"].get("trace_page_size", 50),
    help=t("trace_page_size_help"),
)

# Privacy
st.subheader("Privacy")
telemetry = st.checkbox(
    t("telemetry_label"),
    value=prefs["privacy"].get("telemetry_enabled", True),
    help=t("telemetry_help"),
)
share_adv = st.checkbox(
    t("share_adv_label"),
    value=prefs["privacy"].get("include_advanced_in_share_links", False),
    help=t("share_adv_help"),
)

updated = {
    "version": DEFAULT_PREFS["version"],
    "defaults": {
        "mode": mode,
        "max_tokens": int(max_tokens) if max_tokens is not None else None,
        "budget_limit_usd": float(budget_limit) if budget_limit else None,
        "knowledge_sources": knowledge_sources,
    },
    "ui": {
        "show_trace_by_default": bool(show_trace),
        "auto_export_on_completion": bool(auto_export),
        "trace_page_size": int(trace_page_size),
        "language": prefs["ui"].get("language", "en"),
    },
    "privacy": {
        "telemetry_enabled": bool(telemetry),
        "include_advanced_in_share_links": bool(share_adv),
    },
}

if st.button(t("save_prefs_label"), type="primary", help=t("save_prefs_help")):
    save_prefs(updated)
    flat_old = _flatten(original)
    flat_new = _flatten(updated)
    changed = [k for k, v in flat_new.items() if flat_old.get(k) != v]
    log_event({"event": "settings_changed", "keys_changed": changed, "version": updated["version"]})
    st.success(t("prefs_saved_msg"))
    prefs = updated

if st.button(t("restore_defaults_label"), help=t("restore_defaults_help")):
    save_prefs(DEFAULT_PREFS)
    log_event(
        {
            "event": "settings_changed",
            "keys_changed": list(_flatten(original).keys()),
            "version": DEFAULT_PREFS["version"],
        }
    )
    st.success(t("prefs_restored_msg"))
    prefs = load_prefs()

uploaded = st.file_uploader(t("import_prefs_label"), type="json", help=t("import_prefs_help"))
if uploaded is not None:
    try:
        data = json.load(uploaded)
        save_prefs(data)
        log_event({"event": "settings_imported", "version": data.get("version")})
        st.success(t("prefs_imported_msg"))
        prefs = load_prefs()
    except Exception:
        st.error(t("prefs_invalid_msg"))

if st.download_button(
    t("export_prefs_label"),
    data=json.dumps(prefs).encode("utf-8"),
    file_name="config.json",
    help=t("export_prefs_help"),
):
    log_event({"event": "settings_exported", "version": prefs.get("version")})
