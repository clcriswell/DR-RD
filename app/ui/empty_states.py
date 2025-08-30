import streamlit as st
from .copy import t

def empty_card(title_key: str, body_key: str, *, actions: list[tuple[str, str]] | None = None):
    st.info(f"**{t(title_key)}**\n\n{t(body_key)}")
    clicked = None
    if actions:
        cols = st.columns(len(actions))
        for (label, key), col in zip(actions, cols):
            with col:
                if st.button(label, key=f"empty_{key}", use_container_width=True):
                    clicked = key
    return clicked

def trace_empty():
    return empty_card("trace_empty_title", "trace_empty_body")

def reports_empty():
    return empty_card("reports_empty_title", "reports_empty_body")

def metrics_empty():
    return empty_card("metrics_empty_title", "metrics_empty_body")
