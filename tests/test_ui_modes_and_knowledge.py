import streamlit as st
from utils.run_config import RunConfig, to_session, from_session


def test_ui_knowledge_sources():
    st.session_state.clear()
    cfg = RunConfig(knowledge_sources=["samples", "uploads"])
    to_session(cfg)
    rc = from_session()
    assert set(rc.knowledge_sources) == {"samples", "uploads"}
