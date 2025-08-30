"""Run page for the DR-RD Streamlit application."""

import streamlit as st

from app import main
from utils.telemetry import log_event


def run() -> None:
    """Launch the DR-RD Streamlit application."""
    st.set_page_config(
        page_title="DR-RD",
        page_icon=":material/science:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "DR-RD — AI R&D Workbench"},
    )
    log_event({"event": "nav_page_view", "page": "run"})
    main()


if __name__ == "__main__":
    run()
