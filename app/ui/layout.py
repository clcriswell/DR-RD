import streamlit as st


def section(title: str, help_text: str | None = None):
    st.subheader(title)
    if help_text:
        st.caption(help_text)
    st.divider()


def pad_y(units: int = 1):
    for _ in range(max(1, units)):
        st.write("")

