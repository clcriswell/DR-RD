from dr_rd.utils.token_meter import TokenMeter
from core.budget import BudgetManager
import streamlit as st
from dr_rd.llm_client import call_openai

METER = TokenMeter()
BUDGET: BudgetManager | None = None

ALLOWED_PARAMS = {
    "temperature",
    "response_format",
    "top_p",
}


def set_budget_manager(budget: BudgetManager | None) -> None:
    """Install a :class:`BudgetManager` to enforce spending caps."""
    global BUDGET
    BUDGET = budget


def log_usage(stage, model, pt, ct, cost=0.0):
    if "usage_log" not in st.session_state:
        st.session_state["usage_log"] = []
    st.session_state["usage_log"].append(
        {"stage": stage, "model": model, "pt": pt, "ct": ct, "cost": cost},
    )


def llm_call(client, model_id: str, stage: str, messages: list, **params):
    """Backward-compatible wrapper around :func:`call_openai`."""
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
    chosen_model = model_id
    result = call_openai(model=chosen_model, messages=messages, **safe)
    resp = result["raw"]

    usage_obj = getattr(resp, "usage", None)
    if usage_obj is None and getattr(resp, "choices", None):
        usage_obj = getattr(resp.choices[0], "usage", None)
    if isinstance(usage_obj, dict):
        usage = {
            "prompt_tokens": usage_obj.get("prompt_tokens", 0),
            "completion_tokens": usage_obj.get("completion_tokens", 0),
            "total_tokens": usage_obj.get("total_tokens", 0),
        }
    else:
        usage = {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
            "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }

    cost = 0.0
    try:
        METER.add_usage(chosen_model, stage, usage)
        if BUDGET:
            cost = BUDGET.consume(
                usage["prompt_tokens"], usage["completion_tokens"], chosen_model, stage=stage
            )
    except Exception:
        pass

    log_usage(stage, chosen_model, usage["prompt_tokens"], usage["completion_tokens"], cost)
    return resp
