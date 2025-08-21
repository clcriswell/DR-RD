import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import APIStatusError
import os
import json
from pathlib import Path

from utils.config import load_config

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test"))


def _to_responses_input(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            parts = [{"type": "input_text", "text": content}]
        else:
            parts = content
        converted.append({"role": m.get("role", "user"), "content": parts})
    return converted


def extract_text(resp: Any) -> Optional[str]:
    """Return the main text content from either Responses or Chat responses."""
    if resp is None:
        return None
    # Responses API
    if hasattr(resp, "output") or hasattr(resp, "output_text"):
        if getattr(resp, "output_text", None):
            return getattr(resp, "output_text")
        chunks = []
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", "") == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") == "output_text":
                        chunks.append(getattr(c, "text", ""))
        return "".join(chunks) if chunks else None
    # Chat Completions
    try:
        choice = resp.choices[0]
    except Exception:
        return None
    return getattr(getattr(choice, "message", None), "content", None) or getattr(choice, "text", None)


def call_openai(model: str, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """Call OpenAI with automatic routing between Responses and Chat APIs."""
    cfg = load_config()
    if cfg.get("dry_run", {}).get("enabled", False):
        fixtures_dir = Path(cfg.get("dry_run", {}).get("fixtures_dir", "tests/fixtures"))
        path = fixtures_dir / "llm" / "plan_seed.json"
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return {"raw": data, "text": data.get("text", "")}
        except Exception:
            return {"raw": {}, "text": ""}

    params = dict(kwargs)
    if "max_tokens" in params and "max_output_tokens" not in params:
        params["max_output_tokens"] = params.pop("max_tokens")
    try:
        response_params = {k: v for k, v in params.items() if k != "temperature"}
        try:
            resp = client.responses.create(
                model=model,
                input=_to_responses_input(messages),
                **response_params,
            )
        except TypeError:
            if "response_format" in response_params:
                cleaned = {
                    k: v for k, v in response_params.items() if k != "response_format"
                }
                resp = client.responses.create(
                    model=model,
                    input=_to_responses_input(messages),
                    **cleaned,
                )
            else:
                raise
        text = extract_text(resp)
        logger.info("call_openai: used Responses API for %s", model)
        return {"raw": resp, "text": text}
    except APIStatusError as e:
        if e.status_code != 404:
            raise
        logger.info("call_openai: falling back to Chat Completions for %s", model)
    except Exception as e:
        msg = str(e).lower()
        if "404" not in msg:
            raise
        logger.info("call_openai: falling back to Chat Completions for %s", model)

    params = dict(kwargs)
    if "max_output_tokens" in params and "max_tokens" not in params:
        params["max_tokens"] = params.pop("max_output_tokens")
    resp = client.chat.completions.create(model=model, messages=messages, **params)
    text = extract_text(resp)
    return {"raw": resp, "text": text}
from core.token_meter import TokenMeter
from core.budget import BudgetManager, CostTracker
import streamlit as st

METER = TokenMeter()
BUDGET: BudgetManager | CostTracker | None = None
ENFORCE_BUDGET = False

ALLOWED_PARAMS = {
    "temperature",
    "response_format",
    "top_p",
}


def set_budget_manager(budget: BudgetManager | CostTracker | None) -> None:
    """Install a cost tracker for logging only."""
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
    METER.add_usage(chosen_model, stage, usage)
    if BUDGET:
        cost = BUDGET.consume(
            usage["prompt_tokens"], usage["completion_tokens"], chosen_model, stage=stage
        )

    log_usage(stage, chosen_model, usage["prompt_tokens"], usage["completion_tokens"], cost)
    return resp
