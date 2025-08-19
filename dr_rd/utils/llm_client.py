"""LLM client with budget awareness."""

from dr_rd.utils.token_meter import TokenMeter
from dr_rd.utils import tokenizer
from core.budget import BudgetManager
from openai import BadRequestError
import streamlit as st

METER = TokenMeter()
BUDGET: BudgetManager | None = None

ALLOWED_PARAMS = {
    "temperature",
    "response_format",
    "max_tokens",
    "max_completion_tokens",
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
        {"stage": stage, "model": model, "pt": pt, "ct": ct, "cost": cost}
    )


def llm_call(client, model_id: str, stage: str, messages: list, max_tokens_hint: int | None = None, **params):
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}

    chosen_model = model_id
    est_prompt = tokenizer.estimate(messages)
    est_completion = max(
        64,
        max_tokens_hint
        or safe.get("max_tokens", 0)
        or safe.get("max_completion_tokens", 0)
        or 64,
    )

    key = "max_completion_tokens" if "max_completion_tokens" in params else "max_tokens"
    safe.setdefault(key, est_completion)

    try:
        resp = client.chat.completions.create(model=chosen_model, messages=messages, **safe)
    except BadRequestError as e:  # pragma: no cover - best effort compatibility
        if (
            "max_tokens" in safe
            and "max_tokens" in str(e)
            and "max_completion_tokens" in str(e)
        ):
            safe["max_completion_tokens"] = safe.pop("max_tokens")
            resp = client.chat.completions.create(
                model=chosen_model, messages=messages, **safe
            )
        else:
            raise

    usage_obj = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", None)
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
