from types import SimpleNamespace

import streamlit as st

import core.llm_client as lc
from core.budget import CostTracker


def test_cost_tracking_no_enforcement(monkeypatch):
    st.session_state.clear()
    mode_cfg = {"target_cost_usd": 0.01, "stage_weights": {"synth": 1.0}}
    prices = {"models": {"gpt-5": {"in_per_1k": 0.001, "out_per_1k": 0.001}}}
    tracker = CostTracker(mode_cfg, prices)
    lc.set_budget_manager(tracker)

    resp = SimpleNamespace(
        usage={"prompt_tokens": 10000, "completion_tokens": 0, "total_tokens": 10000}
    )
    monkeypatch.setattr(
        lc, "call_openai", lambda model, messages, **kwargs: {"raw": resp, "text": "ok"}
    )

    lc.llm_call(
        None, "gpt-5", stage="synth", messages=[{"role": "user", "content": "hi"}]
    )
    log = st.session_state["usage_log"][-1]
    assert log["pt"] == 10000
    assert tracker.spend > 0
