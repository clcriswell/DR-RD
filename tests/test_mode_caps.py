import streamlit as st

from core.budget import BudgetManager
from core.llm_client import llm_call, set_budget_manager


class DummyClient:
    class _Chat:
        class _Completions:
            def create(self, model, messages, **params):
                prompt = sum(len(m.get("content", "").split()) for m in messages)
                completion = 0

                class Choice:
                    usage = {
                        "prompt_tokens": prompt,
                        "completion_tokens": completion,
                    }
                    message = type("msg", (), {"content": "ok"})()

                class Resp:
                    choices = [Choice()]

                return Resp()

        completions = _Completions()

    chat = _Chat()


PRICE_TABLE = {
    "models": {
        "gpt-5": {"in_per_1k": 0.00125, "out_per_1k": 0.01000},
    }
}
MODE_CFG = {
    "target_cost_usd": 0.01,
    "stage_weights": {"synth": 1.0},
}


def test_fallback_and_summarize():
    st.session_state.clear()
    budget = BudgetManager(MODE_CFG, PRICE_TABLE)
    set_budget_manager(budget)
    messages = [{"role": "user", "content": "word " * 10000}]
    llm_call(DummyClient(), "gpt-5", stage="synth", messages=messages)
    log = st.session_state["usage_log"][-1]
    # Model remains gpt-5 and cost tracking reflects the full token usage
    assert log["model"] == "gpt-5"
    assert log["pt"] == 10000
    assert budget.spend > budget.target_cost_usd * (1 - budget.safety_margin)
