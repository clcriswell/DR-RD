"""Simple Streamlit interface for running DR-RD multi-agent pipeline."""
import streamlit as st
from core.orchestrator import run_pipeline


def main():
    st.title("DR-RD Multi-Agent Runner")
    idea = st.text_area("Project Idea")
    mode = st.selectbox("Mode", ["test", "balanced", "deep"], index=0)
    if st.button("Run" ):
        if not idea:
            st.warning("Please provide an idea")
        else:
            final, _, trace = run_pipeline(idea, mode=mode)
            st.subheader("Synthesis")
            st.write(final)
            with st.expander("Agent Trace"):
                for item in trace:
                    st.write(f"{item['agent']} ({item['tokens']} tokens): {item['finding']}")


if __name__ == "__main__":  # pragma: no cover
    main()
