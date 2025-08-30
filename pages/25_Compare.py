"""Compare Runs page."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List

import streamlit as st

from app.ui import empty_states
from utils.paths import artifact_path
from utils.runs import list_runs, load_run_meta
from utils.trace_export import flatten_trace_rows
from utils.diff_runs import (
    align_steps,
    diff_metrics,
    diff_table_rows,
    to_csv,
    to_markdown,
)
from utils.telemetry import log_event
from utils.metrics import ensure_run_totals


if st.query_params.get("view") != "compare":
    st.query_params["view"] = "compare"

st.title("Compare Runs")
log_event({"event": "nav_page_view", "page": "compare"})

runs = list_runs(limit=200)
if not runs:
    empty_states.trace_empty()
else:
    labels = {
        r["run_id"]: f"{r['run_id']} — {datetime.fromtimestamp(r['started_at']).isoformat()} — {r['idea_preview'][:40]}…"
        for r in runs
    }
    options = [r["run_id"] for r in runs]
    qp = st.query_params
    run_id_a = qp.get("run_id_a")
    run_id_b = qp.get("run_id_b")

    def _default_other(exclude: str | None) -> str | None:
        for rid in options:
            if rid != exclude:
                return rid
        return None

    if run_id_a and not run_id_b:
        run_id_b = _default_other(run_id_a)
    elif run_id_b and not run_id_a:
        run_id_a = _default_other(run_id_b)
    elif not run_id_a and not run_id_b:
        run_id_a = options[0] if options else None
        run_id_b = _default_other(run_id_a)

    if run_id_a:
        qp["run_id_a"] = run_id_a
    if run_id_b:
        qp["run_id_b"] = run_id_b

    index_a = options.index(run_id_a) if run_id_a in options else 0
    index_b = options.index(run_id_b) if run_id_b in options else (1 if len(options) > 1 else 0)
    sel_a = st.selectbox("Run A", options, index=index_a, format_func=lambda x: labels[x], key="run_a")
    sel_b = st.selectbox("Run B", options, index=index_b, format_func=lambda x: labels[x], key="run_b")
    if sel_a != run_id_a:
        qp["run_id_a"] = sel_a
        st.rerun()
    if sel_b != run_id_b:
        qp["run_id_b"] = sel_b
        st.rerun()
    run_id_a, run_id_b = sel_a, sel_b

    if (
        run_id_a
        and run_id_b
        and st.session_state.get("_compare_opened") != (run_id_a, run_id_b)
    ):
        log_event(
            {
                "event": "compare_opened",
                "run_id_a": run_id_a,
                "run_id_b": run_id_b,
            }
        )
        st.session_state["_compare_opened"] = (run_id_a, run_id_b)

    def _load(run_id: str) -> tuple[dict, List[dict], dict, str]:
        meta = load_run_meta(run_id) or {}
        trace_path = artifact_path(run_id, "trace", "json")
        trace = (
            json.loads(trace_path.read_text(encoding="utf-8"))
            if trace_path.exists()
            else []
        )
        rows = flatten_trace_rows(trace)
        totals = ensure_run_totals(meta, rows)
        summary_path = artifact_path(run_id, "summary", "md")
        summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        return meta, rows, totals, summary

    meta_a, rows_a, totals_a, summary_a = _load(run_id_a)
    meta_b, rows_b, totals_b, summary_b = _load(run_id_b)

    aligned = align_steps(rows_a, rows_b)
    rows = diff_table_rows(aligned)
    summary = diff_metrics(totals_a, totals_b)

    st.subheader("Summary")
    st.table(
        [
            {
                "metric": k,
                "a": v["a"],
                "b": v["b"],
                "delta": v["delta"],
            }
            for k, v in summary.items()
            if k in {"tokens", "cost_usd", "steps", "errors", "duration_ms"}
        ]
    )

    with st.expander("Trace differences", expanded=True):
        filter_text = st.text_input("Filter", key="compare_filter")
        changed_only = st.checkbox("Show only changed rows", key="compare_changed_only")
        prev = (
            st.session_state.get("_compare_filter"),
            st.session_state.get("_compare_changed_only"),
        )
        cur = (filter_text, changed_only)
        if cur != prev:
            log_event(
                {
                    "event": "compare_filter_changed",
                    "run_id_a": run_id_a,
                    "run_id_b": run_id_b,
                    "changed_only": changed_only,
                    "text": filter_text,
                }
            )
            st.session_state["_compare_filter"] = filter_text
            st.session_state["_compare_changed_only"] = changed_only

        def _is_changed(r: dict) -> bool:
            return (
                r["a_status"] != r["b_status"]
                or r["d_dur_ms"]
                or r["d_tokens"]
                or r["d_cost"]
            )

        display_rows = rows
        if changed_only:
            display_rows = [r for r in display_rows if _is_changed(r)]
        if filter_text:
            ft = filter_text.lower()
            display_rows = [r for r in display_rows if ft in (r["name"] or "").lower()]
        st.dataframe(display_rows)

    col1, col2 = st.columns(2)
    if col1.download_button(
        "Download diff CSV", to_csv(rows), file_name="run_diff.csv", use_container_width=True
    ):
        log_event(
            {
                "event": "compare_export_clicked",
                "format": "csv",
                "run_id_a": run_id_a,
                "run_id_b": run_id_b,
            }
        )
    if col2.download_button(
        "Download summary Markdown",
        to_markdown(summary, rows),
        file_name="run_diff.md",
        use_container_width=True,
    ):
        log_event(
            {
                "event": "compare_export_clicked",
                "format": "md",
                "run_id_a": run_id_a,
                "run_id_b": run_id_b,
            }
        )

    if summary_a or summary_b:
        with st.expander("Final summaries"):
            a_col, b_col = st.columns(2)
            a_col.code(summary_a)
            b_col.code(summary_b)
