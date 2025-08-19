import streamlit as st
from dr_rd.utils.llm_client import BUDGET


def require_budget_or_block():
    """Ensure a budget manager is installed or stop execution."""
    if BUDGET is None:
        st.error("Budget manager not installed. Fix config before running.")
        st.stop()
