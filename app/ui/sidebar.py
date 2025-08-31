from __future__ import annotations

import dataclasses
from typing import Any

import streamlit as st

from app.ui_presets import UI_PRESETS
from utils import knowledge_store
from utils.run_config import RunConfig, defaults
from utils.session_store import init_stores
from utils.telemetry import log_event


def render_sidebar() -> RunConfig:
    """Render the sidebar and return the current :class:`RunConfig`."""

    run_store, _ = init_stores()

    if not st.session_state.get("_sidebar_tip_shown"):
        st.sidebar.caption("Settings apply to the next run.")
        st.session_state["_sidebar_tip_shown"] = True

    def _track_change(field: str, value: Any) -> None:
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
        run_store.clear()
        for f in dataclasses.fields(RunConfig):
            st.session_state[f"_{f.name}_prev"] = getattr(cfg, f.name)
        st.session_state["temperature"] = 0.0
        st.session_state["retries"] = 0
        st.session_state["timeout"] = 0
        log_event({"event": "sidebar_reset", "run_id": st.session_state.get("run_id")})

    with st.sidebar:
        st.subheader("Run settings")
        idea = st.text_area(
            "Project idea",
            value=run_store.get("idea", ""),
            key="idea",
            help="What should the agents work on?",
        )
        run_store.set("idea", idea)
        _track_change("idea", idea)
        modes = list(UI_PRESETS.keys())
        current_mode = run_store.get("mode", modes[0])
        mode = st.selectbox(
            "Mode",
            modes,
            index=modes.index(current_mode) if current_mode in modes else 0,
            key="mode",
            help="Choose run mode",
        )
        run_store.set("mode", mode)
        _track_change("mode", mode)

        with st.expander("Knowledge"):
            knowledge_store.init_store()
            builtins = [("Samples", "samples")]
            choices = builtins + knowledge_store.as_choice_list()
            options = [c[1] for c in choices]
            labels = {c[1]: c[0] for c in choices}
            default_sources = [s for s in run_store.get("knowledge_sources", []) if s in options]
            sources = st.multiselect(
                "Sources",
                options,
                default=default_sources,
                key="knowledge_sources",
                format_func=lambda x: labels.get(x, x),
                help="Select knowledge sources",
            )
            run_store.set("knowledge_sources", sources)
            _track_change("knowledge_sources", sources)
            with st.expander("Manage sources"):
                st.caption("Manage advanced sources here.")

        with st.expander("Diagnostics"):
            show_agent_trace = st.checkbox(
                "Show agent trace",
                value=run_store.get("show_agent_trace", False),
                key="show_agent_trace",
                help="Display detailed agent steps",
            )
            run_store.set("show_agent_trace", show_agent_trace)
            _track_change("show_agent_trace", show_agent_trace)
            verbose_planner = st.checkbox(
                "Verbose planner output",
                value=run_store.get("verbose_planner", False),
                key="verbose_planner",
                help="Print planner debug info",
            )
            run_store.set("verbose_planner", verbose_planner)
            _track_change("verbose_planner", verbose_planner)

        with st.expander("Exports"):
            auto_export_trace = st.checkbox(
                "Auto export trace on completion",
                value=run_store.get("auto_export_trace", False),
                key="auto_export_trace",
            )
            run_store.set("auto_export_trace", auto_export_trace)
            _track_change("auto_export_trace", auto_export_trace)
            auto_export_report = st.checkbox(
                "Auto export report on completion",
                value=run_store.get("auto_export_report", False),
                key="auto_export_report",
            )
            run_store.set("auto_export_report", auto_export_report)
            _track_change("auto_export_report", auto_export_report)

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
            _track_change("temperature", st.session_state["temperature"])
            st.session_state.setdefault("retries", 0)
            st.number_input(
                "Retries",
                min_value=0,
                max_value=10,
                step=1,
                key="retries",
                help="Max retries for calls",
            )
            _track_change("retries", st.session_state["retries"])
            st.session_state.setdefault("timeout", 0)
            st.number_input(
                "Timeout (s)",
                min_value=0,
                max_value=3600,
                step=10,
                key="timeout",
                help="Overall timeout in seconds",
            )
            _track_change("timeout", st.session_state["timeout"])

        st.button("Reset to defaults", on_click=_reset, help="Restore default settings")

    data = run_store.as_dict()
    adv: dict[str, Any] = {
        "temperature": st.session_state.get("temperature", 0.0),
        "retries": st.session_state.get("retries", 0),
        "timeout": st.session_state.get("timeout", 0),
    }
    data["advanced"] = adv
    return RunConfig(**data)
