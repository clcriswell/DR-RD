import streamlit as st


def render_dot(dot: str, *, height: int = 520):
    """Render a Graphviz DOT string in Streamlit."""
    try:
        st.graphviz_chart(dot, width="stretch", height=height)
    except Exception:
        st.code(dot, language="dot")
