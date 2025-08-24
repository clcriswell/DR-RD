import inspect
import json
import logging
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import streamlit as st
from openai import APIStatusError, OpenAI
from utils.config import load_config

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
# Some SDK versions lack support for the ``response_format`` parameter on the
# Responses API.  Capture support status at import time so we can gracefully
# omit the argument if unavailable.
_SUPPORTS_RESPONSE_FORMAT = (
    "response_format" in inspect.signature(client.responses.create).parameters
)

# OpenAI "web_search_preview" tool is only supported on specific models.
# Keep this list conservative and explicit to avoid silent failures.
SUPPORTED_OPENAI_SEARCH_MODELS: set[str] = {"gpt-4o-mini", "gpt-4o"}


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _live_search_backend() -> str:
    return (os.getenv("LIVE_SEARCH_BACKEND") or "").strip().lower()


def _openai_web_search_requested(enable_web_search: Optional[bool]) -> bool:
    """
    If caller passes an explicit enable_web_search flag, honor it.
    Otherwise infer from env: ENABLE_LIVE_SEARCH==true and LIVE_SEARCH_BACKEND==openai.
    """

    if enable_web_search is not None:
        return bool(enable_web_search) and _live_search_backend() == "openai"
    return _bool_env("ENABLE_LIVE_SEARCH", False) and _live_search_backend() == "openai"


def _coerce_model_for_openai_search(model: str) -> str:
    """If OpenAI web search is requested but model unsupported, warn and override."""

    if _live_search_backend() != "openai":
        return model
    if model in SUPPORTED_OPENAI_SEARCH_MODELS:
        return model
    logger.warning(
        "OpenAI web search requires one of %s; got '%s'. Overriding to 'gpt-4o-mini'.",
        sorted(SUPPORTED_OPENAI_SEARCH_MODELS),
        model,
    )
    return "gpt-4o-mini"


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


def _to_chat_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            converted_content = content
        else:
            converted_content = ""
            for c in content:
                if isinstance(c, dict) and c.get("type") == "input_text":
                    converted_content += c.get("text", "")
        converted.append({"role": m.get("role", "user"), "content": converted_content})
    return converted


def _sanitize_responses_params(params: dict | None) -> dict:
    p = dict(params or {})
    if "seed" in p:
        p.pop("seed", None)
        logger.info("Ignoring unsupported Responses param: seed")
    return p


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


def _strip_code_fences(s: str) -> str:
    """Remove leading and trailing triple-backtick fences from *s*."""
    s = s.strip()
    if s.startswith("```"):
        s = s[3:]
        if "\n" in s:
            s = s.split("\n", 1)[1]
    if s.endswith("```"):
        s = s[: -3]
    return s.strip()


def extract_planner_payload(resp: Any) -> dict:
    """Extract planner JSON payload from various OpenAI response shapes."""
    # Prefer parsed content from the Responses API if present
    for item in getattr(resp, "output", []) or []:
        if getattr(item, "type", "") != "message":
            continue
        for c in getattr(item, "content", []) or []:
            parsed = getattr(c, "parsed", None) or getattr(c, "json", None)
            if isinstance(parsed, dict):
                return parsed
            text = getattr(c, "text", None) or getattr(c, "output_text", None)
            if text:
                try:
                    return json.loads(_strip_code_fences(text))
                except Exception:
                    continue
    # Fallback to raw output_text on Responses objects
    raw = getattr(resp, "output_text", "") or ""
    if raw:
        try:
            return json.loads(_strip_code_fences(raw))
        except Exception:
            pass
    # Chat Completions fallback
    if getattr(resp, "choices", None):
        try:
            content = getattr(resp.choices[0].message, "content", None)
            if content and content.strip():
                return json.loads(_strip_code_fences(content))
        except Exception:
            pass
    preview = (raw or "")[:200]
    raise ValueError(f"Planner response contained no JSON. preview={preview}")


def responses_json_schema_for(model_cls: Type[Any], name: str) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": model_cls.model_json_schema()},
        "strict": True,
    }


def call_openai(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    response_format: Dict[str, Any] | None = None,
    meta: Dict[str, Any] | None = None,
    response_params: Dict[str, Any] | None = None,
    tools: List[Dict[str, Any]] | None = None,
    tool_choice: Any | None = None,
    enable_web_search: bool | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """Call OpenAI with automatic routing between Responses and Chat APIs."""

    request_id = uuid.uuid4().hex
    t0 = time.monotonic()
    meta = meta or {}
    web_search_requested = _openai_web_search_requested(enable_web_search)
    effective_model = (
        _coerce_model_for_openai_search(model) if web_search_requested else model
    )
    api = kwargs.pop("api", "Responses")

    logger.info(
        "LLM start req=%s model=%s purpose=%s agent=%s",
        request_id,
        effective_model,
        meta.get("purpose"),
        meta.get("agent"),
    )

    http_status_or_exc: int | str = "EXC"
    exc: Exception | None = None
    try:
        compiled_prompt = " \n".join(
            m.get("content", "") if isinstance(m.get("content", ""), str) else ""
            for m in messages
        )
        if os.getenv("DRRD_DRY_RUN", "").lower() in ("1", "true", "yes"):
            stub = _dry_stub(compiled_prompt)
            http_status_or_exc = 0
            return {"raw": {}, "text": stub["text"]}

        cfg = load_config()
        if cfg.get("dry_run", {}).get("enabled", False):
            fixtures_dir = Path(cfg.get("dry_run", {}).get("fixtures_dir", "tests/fixtures"))
            path = fixtures_dir / "llm" / "plan_seed.json"
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                http_status_or_exc = 0
                return {"raw": data, "text": data.get("text", "")}
            except Exception:
                http_status_or_exc = 0
                return {"raw": {}, "text": ""}

        if web_search_requested:
            tools = [{"type": "web_search_preview"}]
            if tool_choice is None:
                tool_choice = "auto"

        params = {**(response_params or {}), **kwargs}
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        use_chat_for_seed = os.getenv("DRRD_USE_CHAT_FOR_SEEDED", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        seed = params.get("seed")
        if (
            seed is not None
            and use_chat_for_seed
            and response_format is None
        ):
            chat_params = {k: v for k, v in params.items() if k != "seed"}
            logger.info("Using chat.completions for seeded request")
            resp = client.chat.completions.create(
                model=model,
                messages=_to_chat_messages(messages),
                seed=seed,
                **chat_params,
            )
            http_status_or_exc = getattr(resp, "http_status", 200)
            text = extract_text(resp)
            return {"raw": resp, "text": text}

        params = _sanitize_responses_params(params)
        if response_format is not None and _SUPPORTS_RESPONSE_FORMAT:
            params["response_format"] = response_format
        mode = None
        try:
            import streamlit as st  # type: ignore

            mode = st.session_state.get("MODE")
        except Exception:
            mode = os.getenv("MODE")
        if params.get("temperature") is None and mode == "test":
            params["temperature"] = 0.0
        if "max_tokens" in params and "max_output_tokens" not in params:
            params["max_output_tokens"] = params.pop("max_tokens")

        resp_params = {k: v for k, v in params.items() if k != "temperature"}
        logger.info("call_openai: model=%s api=Responses", effective_model)
        backoff = 0.1
        for attempt in range(4):
            try:
                resp = client.responses.create(
                    model=effective_model,
                    input=_to_responses_input(messages),
                    **resp_params,
                )
                http_status_or_exc = getattr(resp, "http_status", 200)
                text = extract_text(resp)
                return {"raw": resp, "text": text}
            except APIStatusError as e:
                http_status_or_exc = e.status_code
                if e.status_code not in (404, 429, 500, 502, 503, 504):
                    raise
                if e.status_code == 404:
                    break
                if attempt == 3:
                    raise
                time.sleep(backoff + random.uniform(0, backoff))
                backoff *= 2
            except Exception as e:
                msg = str(e).lower()
                if "404" not in msg:
                    if attempt == 3:
                        raise
                    time.sleep(backoff + random.uniform(0, backoff))
                    backoff *= 2
                    continue
                break

        chat_params = {k: v for k, v in params.items()}
        if response_format is not None:
            chat_params["response_format"] = response_format
        if "max_output_tokens" in chat_params and "max_tokens" not in chat_params:
            chat_params["max_tokens"] = chat_params.pop("max_output_tokens")
        logger.info("call_openai: model=%s api=Chat", effective_model)
        resp = client.chat.completions.create(
            model=effective_model, messages=_to_chat_messages(messages), **chat_params
        )
        http_status_or_exc = getattr(resp, "http_status", 200)
        text = extract_text(resp)
        return {"raw": resp, "text": text}
    except Exception as e:
        exc = e
        raise
    finally:
        duration_ms = int((time.monotonic() - t0) * 1000)
        logger.info(
            "LLM end   req=%s status=%s duration_ms=%d",
            request_id,
            http_status_or_exc,
            duration_ms,
        )


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
    enable_web_search: bool | None = None,
    **params,
):
    """Backward-compatible wrapper around :func:`call_openai`."""
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
    if temperature is not None:
        safe["temperature"] = temperature
    if seed is not None:
        safe["seed"] = seed
    response_format = safe.pop("response_format", None)
    chosen_model = model_id
    result = call_openai(
        model=chosen_model,
        messages=messages,
        response_format=response_format,
        response_params=safe,
        enable_web_search=enable_web_search,
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
