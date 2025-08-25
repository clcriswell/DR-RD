import streamlit as st
from core.model_router import pick_model, CallHints


def test_stage_override_via_mode_cfg():
    st.session_state.clear()
    st.session_state["MODE_CFG"] = {"models": {"plan": "cfg-model"}}
    sel = pick_model(CallHints(stage="plan"))
    assert sel["model"] == "cfg-model"
