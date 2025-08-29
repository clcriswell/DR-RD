import streamlit as st
from dr_rd.prompting.prompt_factory import PromptFactory
from core.agents.unified_registry import AGENT_REGISTRY


def main():
    st.title("DR-RD Minimal")
    task = st.text_input("Task description")
    role = st.selectbox("Role", list(AGENT_REGISTRY.keys()))
    if st.button("Build Prompt"):
        factory = PromptFactory()
        spec = {"role": role, "task": task}
        st.json(factory.build_prompt(spec))


if __name__ == "__main__":
    main()
