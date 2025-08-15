"""Simple Streamlit interface for running DR-RD multi-agent pipeline."""

from app.config_loader import load_mode
from dr_rd.utils.llm_client import set_budget_manager
import uuid, streamlit as st
from core.orchestrator import run_pipeline


def main():
    st.title("DR-RD Multi-Agent Runner")
    idea = st.text_area("Project Idea")
    mode = st.selectbox("Mode", ["test", "balanced", "deep"], index=0)
    if st.button("Run"):
        if not idea:
            st.warning("Please provide an idea")
        else:
            mode_cfg, budget = load_mode(mode)
            set_budget_manager(budget)
            st.session_state["MODE"] = mode
            st.session_state["MODE_CFG"] = mode_cfg

            run_key = (mode, (idea or "").strip())
            if st.session_state.get("LAST_RUN") == run_key:
                st.stop()
            st.session_state["LAST_RUN"] = run_key

            final, _, trace = run_pipeline(idea, mode=mode)
            st.subheader("Synthesis")
            st.write(final)
            with st.expander("Agent Trace"):
                for item in trace:
                    st.write(
                        f"{item['agent']} ({item['tokens']} tokens): {item['finding']}"
                    )


if __name__ == "__main__":  # pragma: no cover
    main()
