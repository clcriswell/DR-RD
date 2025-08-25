"""Helper functions to render a rich Agent Trace in Streamlit.

This module encapsulates the UI for displaying per-agent execution traces,
including a timeline, per-role inspection tabs, token/cost telemetry and
download/export controls. Keeping this logic separate helps maintain a thin
Streamlit entrypoint while providing users with deep insight into how the
pipeline executed their R&D request.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence

import pandas as pd  # type: ignore
import streamlit as st  # type: ignore


def _format_summary(text: str, max_chars: int = 200) -> str:
    """Return a shortened summary of the given text for display.

    We take the first non-empty line and truncate to a maximum number of
    characters. Newlines are preserved in the raw view. If the text is
    longer than ``max_chars`` we append an ellipsis.

    Parameters
    ----------
    text : str
        The full string from which to build a summary.
    max_chars : int, default 200
        Maximum number of characters to include in the summary.

    Returns
    -------
    str
        A one-line summary suitable for brief display.
    """
    if not text:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[: max_chars] + ("…" if len(stripped) > max_chars else "")
    return text[: max_chars] + ("…" if len(text) > max_chars else "")


def render_agent_trace(agent_trace: Sequence[Dict[str, Any]], answers: Dict[str, str]) -> None:
    """Render the agent trace UI.

    This function produces a timeline-style breakdown of each task executed by
    the agents, along with per-role inspection tabs and download controls. It
    should be called from within a Streamlit context (e.g. after executing
    ``execute_plan``) to display the trace to the user.

    Parameters
    ----------
    agent_trace : sequence of dict
        Each dict should at least contain keys ``agent`` (role name), ``title``
        (task title), ``tokens_in``, ``tokens_out``, ``quotes``, ``citations``,
        ``cost``, ``raw_json`` and ``finding``.
    answers : dict
        Mapping from role name to the concatenated outputs for that role. Used
        for populating the per-role inspection tabs.
    """
    # Guard against missing or empty data
    if not agent_trace:
        return
    # Outer expander groups all trace information. An emoji hints at the
    # diagnostics available without taking too much vertical space by default.
    with st.expander("📌 Agent Trace & Inspection", expanded=False):
        total_steps = len(agent_trace)
        # Render each step in order with a progress indicator and summary.
        for idx, item in enumerate(agent_trace, 1):
            agent = item.get("agent", "") or ""
            title = item.get("title", "") or ""
            st.markdown(f"**Step {idx}/{total_steps}: {agent} – {title}**")
            # Progress bar shows progress through the overall plan
            st.progress(min(float(idx) / float(total_steps), 1.0))
            # Token and citation metrics displayed in columns
            cols = st.columns(4)
            cols[0].metric("Tokens in", f"{item.get('tokens_in', 0):,}")
            cols[1].metric("Tokens out", f"{item.get('tokens_out', 0):,}")
            cols[2].metric("Quotes", f"{len(item.get('quotes', []) or [])}")
            cols[3].metric("Citations", f"{len(item.get('citations', []) or [])}")
            # Cost, if present, shown as a caption
            cost = item.get("cost", 0.0) or 0.0
            st.caption(f"**Cost:** ${cost:,.4f}")
            # Show a brief summary of the finding
            summary = _format_summary(item.get("finding", "") or "")
            if summary:
                st.markdown(f"**Summary:** {summary}")
            # Expanders for raw JSON and full output
            with st.expander("🔍 Raw JSON", expanded=False):
                st.json(item.get("raw_json", {}))
            with st.expander("📄 Full Output", expanded=False):
                st.write(item.get("finding", "") or "")

        # Per-role tabs allow users to inspect the aggregated output for each agent
        unique_roles = sorted({item.get("agent", "") for item in agent_trace if item.get("agent")})
        if unique_roles:
            tab_objs = st.tabs(unique_roles)
            for i, role in enumerate(unique_roles):
                with tab_objs[i]:
                    st.subheader(role)
                    role_output = answers.get(role, "")
                    if role_output:
                        st.markdown(role_output)
                    else:
                        st.info("No output recorded for this role.")

        # Horizontal divider before export controls
        st.divider()
        col_json, col_csv = st.columns(2)
        # JSON export: pretty-print the agent trace
        trace_json = json.dumps(list(agent_trace), indent=2, ensure_ascii=False)
        col_json.download_button(
            label="💾 Download Trace (JSON)",
            data=trace_json,
            file_name="agent_trace.json",
            mime="application/json",
        )
        # CSV export: flatten nested structures before conversion
        try:
            flat_rows: List[Dict[str, Any]] = []
            for item in agent_trace:
                row: Dict[str, Any] = {}
                for k, v in item.items():
                    if k in ("quotes", "citations", "raw_json"):
                        row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        row[k] = v
                flat_rows.append(row)
            df = pd.DataFrame(flat_rows)
            col_csv.download_button(
                label="📄 Download Trace (CSV)",
                data=df.to_csv(index=False),
                file_name="agent_trace.csv",
                mime="text/csv",
            )
        except Exception:
            col_csv.caption("CSV export unavailable for this trace.")