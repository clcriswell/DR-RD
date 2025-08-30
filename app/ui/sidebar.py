from __future__ import annotations

import dataclasses
from typing import Any, Dict

import streamlit as st

from app.ui_presets import UI_PRESETS
from utils.run_config import RunConfig, defaults, from_session, to_session
from utils.telemetry import log_event


def render_sidebar() -> RunConfig:
    """Render the sidebar and return the current :class:`RunConfig`."""

    if not st.session_state.get("_run_config_seeded"):
        to_session(defaults())
        st.session_state["_run_config_seeded"] = True
    if not st.session_state.get("_sidebar_tip_shown"):
        st.sidebar.caption("Settings apply to the next run.")
        st.session_state["_sidebar_tip_shown"] = True

    def _track_change(field: str) -> None:
        value = st.session_state[field]
        prev_key = f"_{field}_prev"
        old = st.session_state.get(prev_key)
        if old is None:
            st.session_state[prev_key] = value
            return
        if old != value:
            log_event(
                {
                    "event": "sidebar_changed",
                    "field": field,
                    "old": old,
                    "new": value,
                    "run_id": st.session_state.get("run_id"),
                }
            )
            st.session_state[prev_key] = value

    def _reset() -> None:
        cfg = defaults()
        to_session(cfg)
        for f in dataclasses.fields(RunConfig):
            st.session_state[f"_{f.name}_prev"] = getattr(cfg, f.name)
        st.session_state["temperature"] = 0.0
        st.session_state["retries"] = 0
        st.session_state["timeout"] = 0
        log_event({"event": "sidebar_reset", "run_id": st.session_state.get("run_id")})

    with st.sidebar:
        st.subheader("Run settings")
        st.text_area(
            "Project idea",
            key="idea",
            help="What should the agents work on?",
        )
        _track_change("idea")
        modes = list(UI_PRESETS.keys())
        st.selectbox("Mode", modes, key="mode", help="Choose run mode")
        _track_change("mode")

        with st.expander("Knowledge"):
            st.multiselect(
                "Sources",
                ["local_samples", "uploads", "connectors"],
                key="knowledge_sources",
                help="Select knowledge sources",
            )
            _track_change("knowledge_sources")
            with st.expander("Manage sources"):
                st.caption("Manage advanced sources here.")

        with st.expander("Diagnostics"):
            st.checkbox(
                "Show agent trace",
                key="show_agent_trace",
                help="Display detailed agent steps",
            )
            _track_change("show_agent_trace")
            st.checkbox(
                "Verbose planner output",
                key="verbose_planner",
                help="Print planner debug info",
            )
            _track_change("verbose_planner")

        with st.expander("Exports"):
            st.checkbox(
                "Auto export trace on completion",
                key="auto_export_trace",
            )
            _track_change("auto_export_trace")
            st.checkbox(
                "Auto export report on completion",
                key="auto_export_report",
            )
            _track_change("auto_export_report")

        with st.expander("Advanced options"):
            st.session_state.setdefault("temperature", 0.0)
            st.number_input(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                step=0.1,
                key="temperature",
                help="Sampling temperature",
            )
            _track_change("temperature")
            st.session_state.setdefault("retries", 0)
            st.number_input(
                "Retries",
                min_value=0,
                max_value=10,
                step=1,
                key="retries",
                help="Max retries for calls",
            )
            _track_change("retries")
            st.session_state.setdefault("timeout", 0)
            st.number_input(
                "Timeout (s)",
                min_value=0,
                max_value=3600,
                step=10,
                key="timeout",
                help="Overall timeout in seconds",
            )
            _track_change("timeout")

        st.button("Reset to defaults", on_click=_reset, help="Restore default settings")

    cfg = from_session()
    adv: Dict[str, Any] = {
        "temperature": st.session_state.get("temperature", 0.0),
        "retries": st.session_state.get("retries", 0),
        "timeout": st.session_state.get("timeout", 0),
    }
    data = dataclasses.asdict(cfg)
    data["advanced"] = adv
    return RunConfig(**data)
