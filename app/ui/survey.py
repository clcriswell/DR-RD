"""Survey UI components."""
from __future__ import annotations

from typing import Dict

import streamlit as st

from utils import survey, survey_store
from utils.telemetry import log_event


def render_usage_panel() -> None:
    records = survey_store.load_recent()
    metrics = survey_store.compute_aggregates(records)
    with st.sidebar.expander("Usage & Quality", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("SUS responses", metrics["sus_count"])
            st.metric(
                "Mean SUS",
                f"{metrics['sus_mean']:.1f}" if metrics["sus_count"] else "–",
            )
            st.metric(
                "7d SUS mean",
                f"{metrics['sus_7_day_mean']:.1f}" if metrics["sus_count"] else "–",
            )
        with col2:
            st.metric("SEQ responses", metrics["seq_count"])
            st.metric(
                "Mean SEQ",
                f"{metrics['seq_mean']:.1f}" if metrics["seq_count"] else "–",
            )
            st.metric(
                "7d SEQ mean",
                f"{metrics['seq_7_day_mean']:.1f}" if metrics["seq_count"] else "–",
            )


def maybe_prompt_after_run(run_id: str) -> None:
    key = f"survey_prompted_{run_id}"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    log_event({"event": "survey_shown", "run_id": run_id})

    def _render_forms() -> None:
        sus_tab, seq_tab = st.tabs(["SUS", "Ease"])
        with sus_tab:
            responses: Dict[str, int] = {}
            for qkey, stmt in survey.SUS_ITEMS.items():
                responses[qkey] = st.radio(
                    stmt,
                    [1, 2, 3, 4, 5],
                    horizontal=True,
                    format_func=lambda x: [
                        "Strongly disagree",
                        "Disagree",
                        "Neutral",
                        "Agree",
                        "Strongly agree",
                    ][x - 1],
                    key=f"{run_id}_{qkey}",
                )
            comment = st.text_area("Comments (optional)", key=f"sus_comment_{run_id}")
            if st.button("Submit SUS", key=f"sus_submit_{run_id}"):
                total = survey.score_sus(responses)
                survey_store.save_sus(run_id, responses, total, comment)
                log_event(
                    {
                        "event": "survey_submitted",
                        "run_id": run_id,
                        "instrument": "SUS",
                        "total": total,
                    }
                )
                st.success("Thanks!")
        with seq_tab:
            score = st.radio(
                "Overall, how easy was it to complete this task?",
                list(range(1, 8)),
                horizontal=True,
                key=f"seq_score_{run_id}",
            )
            comment2 = st.text_area("Comments (optional)", key=f"seq_comment_{run_id}")
            if st.button("Submit Ease", key=f"seq_submit_{run_id}"):
                norm = survey.normalize_seq(score)
                survey_store.save_seq(run_id, norm, comment2)
                log_event(
                    {
                        "event": "survey_submitted",
                        "run_id": run_id,
                        "instrument": "SEQ",
                        "score": norm,
                    }
                )
                st.success("Thanks!")

    if hasattr(st, "dialog"):
        with st.dialog("Tell us about this run"):
            _render_forms()
    else:  # pragma: no cover - fallback
        with st.expander("Survey"):
            _render_forms()
