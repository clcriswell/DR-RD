from __future__ import annotations

from typing import Any, Dict, List, Sequence

import json
import streamlit as st

from utils import trace_export
from utils.paths import artifact_path
from utils.telemetry import log_event
from utils.session_store import SessionStore

PHASE_LABELS = {
    "planner": "Planner",
    "executor": "Executor",
    "synth": "Synthesizer",
}
STATUS_ICONS = {"complete": "✅", "error": "⚠️", "running": "⏳"}


def _normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Best effort adapter for varying trace shapes."""
    return {
        "phase": (step.get("phase") or step.get("stage") or "executor").lower(),
        "name": step.get("name") or step.get("title") or step.get("role") or "step",
        "status": step.get("status") or ("error" if step.get("error") else "complete"),
        "started_at": step.get("started_at") or step.get("ts_start"),
        "ended_at": step.get("ended_at") or step.get("ts_end"),
        "duration_ms": step.get("duration_ms")
        or step.get("duration")
        or (step.get("duration_s", 0) * 1000 if step.get("duration_s") else None),
        "tokens": step.get("tokens") or step.get("tokens_out") or step.get("tokens_in"),
        "cost": step.get("cost") or step.get("cost_usd"),
        "summary": step.get("summary") or step.get("finding") or step.get("output"),
        "raw": step.get("raw") or step.get("raw_json") or step.get("events"),
        "step_id": step.get("step_id") or step.get("task_id") or step.get("id"),
        "error": step.get("error"),
    }


def render_trace(
    trace: Sequence[Dict[str, Any]],
    run_id: str | None = None,
    *,
    default_view: str = "summary",
    default_query: str = "",
    page_size: int = 25,
) -> None:
    steps = [_normalize_step(s) for s in trace]
    if not steps:
        st.markdown("### No trace yet")
        st.caption("Run the pipeline to see step by step output.")
        return

    total_steps = len(steps)

    page_key = f"trace_page_{run_id}"
    show_all_key = f"trace_show_all_{run_id}"
    page = st.session_state.get(page_key, 1)
    show_all = st.session_state.get(show_all_key, False)
    limit = total_steps if show_all else page_size * page

    view_store = SessionStore(
        "view",
        defaults={"trace_view": "summary", "trace_query": "", "palette_open": False},
        persist_keys={"trace_view", "trace_query"},
    )
    view_val = view_store.get("trace_view", default_view)
    view_opts = ["Summary", "Raw", "Both"]
    view_index = view_opts.index(view_val.capitalize()) if view_val.capitalize() in view_opts else 0
    view = st.radio("View", view_opts, index=view_index, horizontal=True)
    if view.lower() != view_val:
        view_store.set("trace_view", view.lower())

    query_val = view_store.get("trace_query", default_query)
    query = st.text_input(
        "Filter steps", value=query_val, placeholder="Search in name or text…",
    )
    if query != query_val:
        view_store.set("trace_query", query)
    phase_names = ["All"] + [PHASE_LABELS[p] for p in PHASE_LABELS]
    jump = st.radio("Jump to", phase_names, horizontal=True, index=0)

    # telemetry for filter changes
    state_key = "_trace_filter_state"
    state_val = (view, query, jump)
    if st.session_state.get(state_key) != state_val:
        log_event(
            {
                "event": "trace_filter_changed",
                "view": view.lower(),
                "query_len": len(query),
                "phase_scope": jump.lower(),
            }
        )
        st.session_state[state_key] = state_val
        if st.query_params.get("trace_view") != view.lower():
            st.query_params["trace_view"] = view.lower()
        prev_q = st.query_params.get("q", "")
        if query.strip():
            if query != prev_q:
                st.query_params["q"] = query[:100]
        elif prev_q:
            del st.query_params["q"]

    expand_key = "_trace_expand"
    expand_state = st.session_state.get(expand_key) or {p: True for p in PHASE_LABELS}
    col_a, col_b = st.columns(2)
    if col_a.button("Expand all"):
        expand_state = {p: True for p in PHASE_LABELS}
    if col_b.button("Collapse all"):
        expand_state = {p: False for p in PHASE_LABELS}
    if jump != "All":
        target = [k for k, v in PHASE_LABELS.items() if v == jump][0]
        expand_state = {p: p == target for p in PHASE_LABELS}
    st.session_state[expand_key] = expand_state

    # filter steps
    q = query.lower().strip()
    filtered_steps: List[Dict[str, Any]] = []
    for s in steps:
        haystack = " ".join(
            [
                s.get("name", ""),
                s.get("summary", ""),
                json.dumps(s.get("raw"), ensure_ascii=False) if isinstance(s.get("raw"), dict) else str(s.get("raw", "")),
            ]
        ).lower()
        if q and q not in haystack:
            continue
        filtered_steps.append(s)
    st.caption(f"{len(filtered_steps)} of {total_steps} steps")

    # export buttons
    col_json, col_csv, col_md = st.columns(3)
    if col_json.download_button(
        "Download full trace (.json)",
        data=trace_export.to_json(steps),
        file_name=artifact_path(run_id or "session", "trace", "json").name,
        mime="application/json",
    ):
        log_event({"event": "trace_export_clicked", "format": "json", "step_count": len(steps)})
    if col_csv.download_button(
        "Download summary (.csv)",
        data=trace_export.to_csv(steps, run_id=run_id),
        file_name=artifact_path(run_id or "session", "summary", "csv").name,
        mime="text/csv",
    ):
        log_event({"event": "trace_export_clicked", "format": "csv", "step_count": len(steps)})
    if col_md.download_button(
        "Download readable report (.md)",
        data=trace_export.to_markdown(steps, run_id=run_id),
        file_name=artifact_path(run_id or "session", "trace", "md").name,
        mime="text/markdown",
    ):
        log_event({"event": "trace_export_clicked", "format": "md", "step_count": len(steps)})

    # group and render
    groups: Dict[str, List[Dict[str, Any]]] = {p: [] for p in PHASE_LABELS}
    for s in filtered_steps:
        groups.setdefault(s["phase"], []).append(s)

    shown = 0
    for phase, label in PHASE_LABELS.items():
        phase_steps = groups.get(phase) or []
        if not phase_steps:
            continue
        display_steps = phase_steps if show_all else phase_steps[:limit]
        shown += len(display_steps)
        expander = st.expander(label, expanded=expand_state.get(phase, False))
        with expander:
            total = len(phase_steps)
            for idx, step in enumerate(display_steps, 1):
                status = STATUS_ICONS.get(step["status"], step["status"])
                meta: List[str] = []
                if step.get("duration_ms") is not None:
                    meta.append(f"{step['duration_ms']} ms")
                if step.get("tokens") is not None:
                    meta.append(f"{step['tokens']} tok")
                if step.get("cost") is not None:
                    meta.append(f"${step['cost']:.4f}")
                header = f"Step {idx}/{total} — {step['name']} {status}".rstrip()
                if meta:
                    header += " — " + ", ".join(meta)
                st.markdown(f"**{header}**")
                if step["status"] == "error":
                    st.error(step.get("summary") or "Error")
                    with st.expander("Show details", expanded=False):
                        if isinstance(step.get("raw"), dict):
                            st.json(step.get("raw"))
                        else:
                            st.code(str(step.get("raw")), language=None)
                    continue
                if view in ("Summary", "Both"):
                    st.code(step.get("summary") or "", language=None)
                if view in ("Raw", "Both"):
                    raw = step.get("raw")
                    if isinstance(raw, dict):
                        st.json(raw)
                    else:
                        st.code("" if raw is None else str(raw), language=None)

    if not show_all and shown < len(filtered_steps):
        if st.button("Load more", key=f"more_{run_id}", use_container_width=True):
            st.session_state[page_key] = page + 1
            log_event(
                {
                    "event": "trace_page_changed",
                    "page": page + 1,
                    "page_size": page_size,
                    "total_steps": len(filtered_steps),
                }
            )

    prev_show_all = show_all
    show_all_new = st.checkbox("Show all", key=show_all_key, value=show_all)
    if show_all_new != prev_show_all:
        st.session_state[show_all_key] = show_all_new
        log_event(
            {
                "event": "trace_page_changed",
                "page": 0 if show_all_new else st.session_state.get(page_key, 1),
                "page_size": page_size,
                "total_steps": len(filtered_steps),
            }
        )

