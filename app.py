"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
provides a small router that can either launch the main application or
invoke additional tools.
"""

from app import main
import streamlit as st


def tool_router():
    """Route to the main app."""
    tool = st.sidebar.selectbox("Action", ["app"], index=0)

    if tool == "app":
        main()


if __name__ == "__main__":
    tool_router()
