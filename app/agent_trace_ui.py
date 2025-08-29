"""Helper functions to render Agent Trace views in Streamlit."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
from core import trace_export
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


def render_agent_trace(agent_trace: Sequence[Dict[str, Any]], answers: Dict[str, str]) -> None:
    """Render the agent execution timeline and raw outputs."""
    if not agent_trace:
        return
    with st.expander("📌 Agent Trace & Inspection", expanded=False):
        total_steps = len(agent_trace)
        for idx, item in enumerate(agent_trace, 1):
            agent = item.get("role") or item.get("agent") or ""
            title = item.get("title", "")
            st.markdown(f"**Step {idx}/{total_steps}: {agent} – {title}**")
            st.progress(min(float(idx) / float(total_steps), 1.0))
            cols = st.columns(4)
            cols[0].metric("Tokens in", f"{item.get('tokens_in', 0):,}")
            cols[1].metric("Tokens out", f"{item.get('tokens_out', 0):,}")
            cols[2].metric("Quotes", f"{len(item.get('quotes', []) or [])}")
            cols[3].metric("Citations", f"{len(item.get('citations', []) or [])}")
            cost = float(item.get("cost_usd", item.get("cost", 0.0)) or 0.0)
            st.caption(f"**Cost:** ${cost:,.4f}")
            summary = _format_summary(item.get("finding", "") or "")
            if summary:
                st.markdown(f"**Summary:** {summary}")
            with st.expander("🔍 Raw JSON", expanded=False):
                st.json(item.get("raw_json", {}))
            with st.expander("📄 Full Output", expanded=False):
                st.write(item.get("finding", "") or "")
        with st.expander("Span Tree", expanded=False):
            st.json(trace_export.to_tree(agent_trace))

        with st.expander("Metrics", expanded=False):
            from pathlib import Path

            summary_path = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry")) / "summary.json"
            if summary_path.exists():
                st.json(json.loads(summary_path.read_text()))
            else:
                st.write("No telemetry summary found")


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


def render_exports(project_id: str, agent_trace: Sequence[Dict[str, Any]]) -> None:
    """Expose trace/report downloads and shareable links."""
    if not agent_trace:
        return
    st.subheader("Exports")
    col_json, col_csv = st.columns(2)
    trace_json = json.dumps(list(agent_trace), indent=2, ensure_ascii=False)
    col_json.download_button(
        "💾 Download Trace (JSON)",
        data=trace_json,
        file_name="agent_trace.json",
        mime="application/json",
    )
    try:
        flat_rows: List[Dict[str, Any]] = []
        for item in agent_trace:
            row: Dict[str, Any] = {}
            for k, v in item.items():
                if k in ("quotes", "citations", "raw_json", "events"):
                    row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    row[k] = v
            flat_rows.append(row)
        df = pd.DataFrame(flat_rows)
        col_csv.download_button(
            "📄 Download Trace (CSV)",
            data=df.to_csv(index=False),
            file_name="agent_trace.csv",
            mime="text/csv",
        )
    except Exception:
        col_csv.caption("CSV export unavailable for this trace.")
    col_speed, col_chrome = st.columns(2)
    col_speed.download_button(
        "Speedscope JSON",
        data=json.dumps(trace_export.to_speedscope(agent_trace), indent=2),
        file_name="trace.speedscope.json",
        mime="application/json",
    )
    col_chrome.download_button(
        "Chrome Trace JSON",
        data=json.dumps(trace_export.to_chrometrace(agent_trace), indent=2),
        file_name="trace.chrome.json",
        mime="application/json",
    )
    evidence_path = Path("audits") / project_id / "evidence.json"
    coverage_path = Path("audits") / project_id / "coverage.csv"
    if evidence_path.exists():
        st.download_button(
            "Evidence JSON",
            data=evidence_path.read_bytes(),
            file_name="evidence.json",
            mime="application/json",
        )
    if coverage_path.exists():
        st.download_button(
            "Coverage CSV",
            data=coverage_path.read_bytes(),
            file_name="coverage.csv",
            mime="text/csv",
        )
    paths = st.session_state.get("final_paths", {})
    if paths.get("report"):
        st.download_button(
            "Download final report (MD)",
            data=open(paths["report"], "rb"),
            file_name="final_report.md",
        )
    if paths.get("bundle"):
        st.download_button(
            "Download bundle (ZIP)",
            data=open(paths["bundle"], "rb"),
            file_name="final_bundle.zip",
        )
    if project_id:
        st.markdown("---")
        share_path = f"rd_projects/{project_id}"
        st.text("Shareable Project Link")
        st.code(share_path, language=None)
        console_base = os.getenv("CONSOLE_BASE_URL", "").strip()
        if console_base:
            st.markdown(
                f"[Open in Console]({console_base.rstrip('/')}/{project_id})"
            )


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
