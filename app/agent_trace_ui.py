"""Helper functions to render Agent Trace views in Streamlit."""

from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st  # type: ignore
from core import ui_bridge


def _format_summary(text: Any, max_chars: int = 200) -> str:
    """Return a shortened summary of the given text for display.

    ``answers`` values may be either plain strings or structured dictionaries
    (e.g., with a ``content`` field).  This helper now defensively handles both
    cases by extracting a representative string before truncating.
    """
    if not text:
        return ""

    if isinstance(text, dict):
        # Prefer an explicit content/summary field if available; otherwise
        # fall back to a JSON representation so something meaningful is shown.
        text = text.get("content") or text.get("summary") or json.dumps(text, ensure_ascii=False)
    elif not isinstance(text, str):
        text = str(text)

    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[: max_chars] + ("…" if len(stripped) > max_chars else "")
    return text[: max_chars] + ("…" if len(text) > max_chars else "")


def render_live_status(live_status: Dict[str, Dict[str, Any]]) -> None:
    """Show per-task live progress and token counters."""
    if not live_status:
        return
    st.subheader("Live Status")
    for tid, info in live_status.items():
        st.markdown(f"**{info.get('role', '')} – {info.get('title', '')}**")
        st.progress(float(info.get("progress", 0.0)))
        cols = st.columns(3)
        cols[0].metric("Tokens in", f"{info.get('tokens_in', 0):,}")
        cols[1].metric("Tokens out", f"{info.get('tokens_out', 0):,}")
        cols[2].metric("Cost", f"${info.get('cost_usd', 0.0):.4f}")


def render_role_summaries(answers: Dict[str, str]) -> None:
    """Display per-role outputs with raw view toggles."""
    if not answers:
        return
    roles = list(answers.keys())
    tabs = st.tabs(roles)
    for i, role in enumerate(roles):
        with tabs[i]:
            summary = _format_summary(answers.get(role, ""))
            if summary:
                st.markdown(summary)
            with st.expander("View raw", expanded=False):
                st.write(answers.get(role, ""))

def render_trace_diff_panel() -> None:
    """Render cross-run diff and incident bundle controls."""
    runs = ui_bridge.list_runs()
    if len(runs) < 2:
        return
    st.subheader("Run Diff")
    base = st.selectbox("Base Run", runs, format_func=lambda r: f"{r['id']}" )
    cand = st.selectbox("Candidate Run", runs, format_func=lambda r: f"{r['id']}")
    if st.button("Diff Runs"):
        diff = ui_bridge.diff_runs(base["path"], cand["path"])
        st.json(diff)
        red = ui_bridge.redaction_summary(cand["path"])
        with st.expander("Redaction Summary", expanded=False):
            st.json(red)
    if st.button("Export Incident Bundle"):
        path = ui_bridge.make_incident_bundle(base["path"], cand["path"], "incident_bundles")
        st.success(f"Bundle created: {path}")

