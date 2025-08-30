"""Run comparison UI page."""

from __future__ import annotations

import streamlit as st

from utils import compare
from utils.runs import run_options
from utils.telemetry import compare_export_clicked, compare_opened

st.set_page_config(page_title="Compare Runs")

opts, labels = run_options(limit=200)
qp = st.query_params
run_a = qp.get("run_a") or (opts[0] if opts else None)
run_b = qp.get("run_b") or (opts[1] if len(opts) > 1 else None)

col_a, col_b = st.columns(2)
sel_a = col_a.selectbox(
    "Run A",
    opts,
    index=opts.index(run_a) if run_a in opts else 0,
    format_func=lambda x: labels.get(x, x),
)
sel_b = col_b.selectbox(
    "Run B",
    opts,
    index=opts.index(run_b) if run_b in opts else 0,
    format_func=lambda x: labels.get(x, x),
)if sel_a != run_a or sel_b != run_b:
    qp["run_a"] = sel_a
    qp["run_b"] = sel_b
    st.rerun()
run_a, run_b = sel_a, sel_b

if run_a and run_b:
    compare_opened(run_a, run_b)
    a = compare.load_run(run_a)
    b = compare.load_run(run_b)
    cfg = compare.diff_configs(a["lock"], b["lock"])
    mets = compare.diff_metrics(a["totals"], b["totals"])
    aligned = compare.align_steps(a["trace_rows"], b["trace_rows"])

    st.subheader("Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tokens", mets["tokens"]["b"], delta=mets["tokens"]["delta"])
    c2.metric("Cost USD", mets["cost_usd"]["b"], delta=mets["cost_usd"]["delta"])
    c3.metric("Duration s", mets["duration_s"]["b"], delta=mets["duration_s"]["delta"])

    st.subheader("Config changes")
    if cfg:
        st.table([{ "path": p, "a": a_val, "b": b_val } for p, a_val, b_val in cfg])
    else:
        st.caption("No config differences")

    st.subheader("Trace alignment")
    rows = []
    for step in aligned:
        diff = compare.diff_steps(step.a, step.b)
        phase = (step.a or step.b).get("phase") if (step.a or step.b) else ""
        rows.append(
            {
                "phase": phase,
                "a_name": step.a.get("name") if step.a else None,
                "b_name": step.b.get("name") if step.b else None,
                "a_status": diff["a_status"],
                "b_status": diff["b_status"],
                "d_duration_ms": diff["d_duration_ms"],
                "d_tokens": diff["d_tokens"],
                "d_cost": diff["d_cost"],
                "similarity": f"{diff['summary_ratio']*100:.1f}%",
            }
        )
    st.dataframe(rows)

    md = compare.to_markdown(a, b, cfg, mets, aligned)
    if st.download_button(
        "Download diff (.md)",
        data=md.encode("utf-8"),
        file_name=f"compare_{run_a}_{run_b}.md",
        use_container_width=True,
    ):
        compare_export_clicked(run_a, run_b, "md")
