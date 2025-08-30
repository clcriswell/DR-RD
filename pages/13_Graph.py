"""Trace Graph viewer."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

try:  # thin import; avoid heavy failures
    from app.ui.graph import render_dot
except Exception:  # pragma: no cover
    def render_dot(dot: str, *, height: int = 520) -> None:  # type: ignore
        st.code(dot, language="dot")

from utils.graph.trace_graph import build_graph, critical_path, to_dot
try:
    from utils.paths import artifact_path
except Exception:  # pragma: no cover
    from pathlib import Path

    def artifact_path(run_id: str, name: str, ext: str) -> Path:
        return Path(".dr_rd") / "runs" / run_id / f"{name}.{ext}"

try:
    from utils.runs import list_runs, last_run_id
except Exception:  # pragma: no cover
    def list_runs(limit: int = 100) -> list:  # type: ignore
        return []

    def last_run_id() -> str | None:  # type: ignore
        return None

from utils.trace_export import flatten_trace_rows
from utils.telemetry import log_event, graph_view_opened, graph_export_clicked

st.title("Trace Graph")
log_event({"event": "nav_page_view", "page": "graph"})

runs = list_runs(limit=100)
if not runs:
    st.info("No runs found.")
else:
    labels = {
        r["run_id"]: f"{r['run_id']} — {datetime.fromtimestamp(r['started_at']).isoformat()}" for r in runs
    }
    options = list(labels.keys())
    run_id = last_run_id() or (options[0] if options else "")
    index = options.index(run_id) if run_id in options else 0
    selected = st.selectbox("Run", options, index=index, format_func=lambda x: labels[x])
    run_id = selected

    trace_path = artifact_path(run_id, "trace", "json")
    trace = json.loads(trace_path.read_text("utf-8")) if trace_path.exists() else []
    rows = flatten_trace_rows(trace)

    nodes, edges = build_graph(rows)
    phases = sorted({n.phase for n in nodes if n.phase})
    sel_phases = st.multiselect("Phases", phases, default=phases)
    show_data = st.checkbox("Show data edges", value=True)
    hi_cp = st.checkbox("Highlight critical path", value=False)

    nodes = [n for n in nodes if n.phase in sel_phases]
    node_ids = {n.id for n in nodes}
    edges = [e for e in edges if e.src in node_ids and e.dst in node_ids and (show_data or e.kind != "data")]

    highlight = critical_path(nodes, edges) if hi_cp else []
    dot = to_dot(nodes, edges, highlight=highlight)
    render_dot(dot)

    graph_view_opened(run_id)

    col1, col2 = st.columns(2)
    with col1:
        if st.download_button("Download .dot", dot, file_name=f"{run_id}_graph.dot", mime="text/vnd.graphviz"):
            graph_export_clicked(run_id, "dot")
    with col2:
        png_bytes = None
        try:
            import graphviz

            png_bytes = graphviz.Source(dot).pipe(format="png")
        except Exception:
            png_bytes = None
        if png_bytes and st.download_button(
            "Download .png", png_bytes, file_name=f"{run_id}_graph.png", mime="image/png"
        ):
            graph_export_clicked(run_id, "png")
