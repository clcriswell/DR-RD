import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import time
from openai import APIStatusError, OpenAI
from utils.config import load_config
import streamlit as st
from core.budget import BudgetManager, CostTracker
from core.token_meter import TokenMeter

logger = logging.getLogger(__name__)

seed_env = os.getenv("DRRD_SEED")
if seed_env:
    try:
        random.seed(int(seed_env))
    except ValueError:
        pass

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test"))


def _dry_stub(prompt: str) -> dict:
    return {"text": "[DRY_RUN] " + (prompt[:200] if isinstance(prompt, str) else "ok")}


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
    return getattr(getattr(choice, "message", None), "content", None) or getattr(
        choice, "text", None
    )


def responses_json_schema_for(model_cls: Type[Any], name: str) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": model_cls.model_json_schema()},
        "strict": True,
    }


def call_openai(
    model: str,
    messages: List[Dict[str, Any]],
    *,
    seed: int | None = None,
    temperature: float | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """Call OpenAI with automatic routing between Responses and Chat APIs."""
    compiled_prompt = " \n".join(
        m.get("content", "") if isinstance(m.get("content", ""), str) else "" for m in messages
    )
    if os.getenv("DRRD_DRY_RUN", "").lower() in ("1", "true", "yes"):
        stub = _dry_stub(compiled_prompt)
        return {"raw": {}, "text": stub["text"]}

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
    mode = None
    try:
        import streamlit as st  # type: ignore

        mode = st.session_state.get("MODE")
    except Exception:
        mode = os.getenv("MODE")
    if temperature is None and mode == "test":
        params["temperature"] = 0.0
    elif temperature is not None:
        params["temperature"] = temperature
    if seed is not None:
        params["seed"] = seed
    if "max_tokens" in params and "max_output_tokens" not in params:
        params["max_output_tokens"] = params.pop("max_tokens")
    backoff = 0.1
    for attempt in range(4):
        try:
            response_params = {k: v for k, v in params.items() if k != "temperature"}
            try:
                logger.info("call_openai: model=%s, api=Responses", model)
                resp = client.responses.create(
                    model=model,
                    input=_to_responses_input(messages),
                    **response_params,
                )
            except TypeError:
                if "response_format" in response_params:
                    cleaned = {k: v for k, v in response_params.items() if k != "response_format"}
                    logger.info("call_openai: model=%s, api=Responses", model)
                    resp = client.responses.create(
                        model=model,
                        input=_to_responses_input(messages),
                        **cleaned,
                    )
                else:
                    raise
            text = extract_text(resp)
            return {"raw": resp, "text": text}
        except APIStatusError as e:
            if e.status_code not in (404, 429, 500, 502, 503, 504):
                raise
            if e.status_code == 404:
                logger.info("call_openai: falling back to Chat Completions")
                break
            if attempt == 3:
                logger.error("call_openai: failed after retries for %s", model)
                raise
            time.sleep(backoff + random.uniform(0, backoff))
            backoff *= 2
        except Exception as e:
            msg = str(e).lower()
            if "404" not in msg:
                if attempt == 3:
                    logger.error("call_openai: failed after retries for %s", model)
                    raise
                time.sleep(backoff + random.uniform(0, backoff))
                backoff *= 2
                continue
            logger.info("call_openai: falling back to Chat Completions")
            break

    params = dict(kwargs)
    if "max_output_tokens" in params and "max_tokens" not in params:
        params["max_tokens"] = params.pop("max_output_tokens")
    logger.info("call_openai: model=%s, api=ChatCompletions", model)
    resp = client.chat.completions.create(model=model, messages=messages, **params)
    text = extract_text(resp)
    return {"raw": resp, "text": text}


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


def llm_call(
    client,
    model_id: str,
    stage: str,
    messages: list,
    seed: int | None = None,
    temperature: float | None = None,
    **params,
):
    """Backward-compatible wrapper around :func:`call_openai`."""
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
    chosen_model = model_id
    result = call_openai(
        model=chosen_model,
        messages=messages,
        seed=seed,
        temperature=temperature,
        **safe,
    )
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
    try:
        setattr(resp, "tokens_in", usage["prompt_tokens"])
        setattr(resp, "tokens_out", usage["completion_tokens"])
        setattr(resp, "cost_usd", cost)
    except Exception:
        pass
    return resp
