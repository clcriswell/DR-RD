from __future__ import annotations

import streamlit as st
from core.orchestrator import run_pipeline

def render_lite(mode: str) -> None:
    st.header("DR‑RD Lite")

    idea = st.text_area("Project Idea", key="lite_idea")

    if st.button("Run", key="lite_run"):
        if not idea:
            st.warning("Please provide an idea")
            st.stop()

        run_key = (mode, (idea or "").strip())
        if st.session_state.get("LITE_LAST_RUN") == run_key:
            st.stop()
        st.session_state["LITE_LAST_RUN"] = run_key

        final, _, trace = run_pipeline(idea, mode=mode)

        st.subheader("Synthesis")
        st.write(final)

        with st.expander("Agent Trace", expanded=False):
            for item in (trace or []):
                agent = item.get("agent", "?")
                tokens = item.get("tokens", "?")
                finding = item.get("finding", "")
                st.write(f"{agent} ({tokens} tokens): {finding}")
