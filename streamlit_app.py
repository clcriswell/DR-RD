"""Simple Streamlit interface for running DR-RD agents."""
import streamlit as st
from app.agent_runner import run_agent


def main():
    st.title("DR-RD Agent Runner")
    role = st.text_input("Role")
    prompt = st.text_area("Prompt")
    depth = st.selectbox("Design Depth", ["Low", "Medium", "High"], index=0)
    if st.button("Run"):
        if not role or not prompt:
            st.warning("Please provide role and prompt")
        else:
            result = run_agent(role, prompt, depth)
            st.write(result)


if __name__ == "__main__":  # pragma: no cover
    main()
