import streamlit as st
from core.model_router import pick_model, CallHints


def test_stage_override_via_mode_cfg():
    st.session_state.clear()
    st.session_state["MODE_CFG"] = {"models": {"plan": "cfg-model"}}
    sel = pick_model(CallHints(stage="plan"))
    assert sel["model"] == "cfg-model"


def test_test_mode_has_no_effect():
    st.session_state.clear()
    h = CallHints(stage="exec")
    sel_base = pick_model(h)
    st.session_state["final_flags"] = {"TEST_MODE": True}
    sel_test = pick_model(h)
    assert sel_test == sel_base
    assert "temperature" not in sel_test["params"]
    st.session_state["final_flags"]["TEST_MODE"] = False
    sel_again = pick_model(h)
    assert sel_again == sel_base
