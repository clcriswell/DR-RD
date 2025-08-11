"""LLM client with budget awareness."""

from dr_rd.utils.token_meter import TokenMeter
from dr_rd.utils import tokenizer
from core.budget import BudgetManager, BudgetExhausted
import streamlit as st
import logging

METER = TokenMeter()
BUDGET: BudgetManager | None = None

ALLOWED_PARAMS = {"temperature", "response_format", "max_tokens", "top_p"}


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


def _cheaper_model(stage: str, current: str) -> str | None:
    fallbacks = {
        "synth": ["gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "exec": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "plan": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
    }
    seq = fallbacks.get(stage, [])
    if current not in seq:
        return None
    idx = seq.index(current)
    return seq[idx + 1] if idx + 1 < len(seq) else None


def _summarize_messages(messages: list, target: int) -> list:
    """Truncate message contents to roughly ``target`` tokens."""
    out = []
    for m in messages:
        words = m.get("content", "").split()
        if len(words) > target:
            words = words[:target]
        out.append({**m, "content": " ".join(words)})
    return out


def llm_call(client, model_id: str, stage: str, messages: list, max_tokens_hint: int | None = None, **params):
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}

    chosen_model = model_id
    est_prompt = tokenizer.estimate(messages)
    est_completion = max(64, max_tokens_hint or safe.get("max_tokens", 0) or 64)

    if BUDGET:
        while not BUDGET.can_afford(stage, chosen_model, est_prompt, est_completion):
            cheaper = _cheaper_model(stage, chosen_model)
            if cheaper:
                logging.info(f"budget fallback: {chosen_model} -> {cheaper}")
                chosen_model = cheaper
                continue
            if est_prompt > 20:
                messages = _summarize_messages(messages, max(1, int(est_prompt * 0.8)))
                est_prompt = tokenizer.estimate(messages)
                continue
            est_completion = max(16, int(est_completion * 0.8))
            if est_completion <= 16:
                raise BudgetExhausted("Unable to fit call under budget")

        safe["max_tokens"] = min(est_completion, BUDGET.remaining_tokens(chosen_model, "completion"))

    resp = client.chat.completions.create(model=chosen_model, messages=messages, **safe)

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
