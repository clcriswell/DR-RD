import streamlit as st
from utils.run_config import RunConfig, to_session, from_session


def test_ui_modes_and_knowledge():
    st.session_state.clear()
    cfg = RunConfig(mode="standard", knowledge_sources=["samples", "uploads"])
    to_session(cfg)
    rc = from_session()
    assert rc.mode == "standard"
    assert set(rc.knowledge_sources) == {"samples", "uploads"}
