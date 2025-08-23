import json
import os
import typing as t
from dataclasses import dataclass

from utils.logging import logger, safe_exc

from core.llm_client import call_openai
from core.privacy import redact_for_logging
from core.prompt_utils import coerce_user_content


def select_model(
    purpose: str, ui_model: str | None = None, agent_name: str | None = None
) -> str:
    """Resolve the model to use based on UI, agent, or env settings."""

    model: str | None = ui_model.strip() if ui_model else None

    if not model and agent_name:
        import re

        env_name = re.sub(r"[^0-9A-Za-z]+", "_", agent_name.upper())
        agent_env = os.getenv(f"DRRD_MODEL_AGENT_{env_name}")
        if agent_env:
            model = agent_env.strip()

    if not model:
        env_purpose = os.getenv(f"DRRD_MODEL_{purpose.upper()}")
        if env_purpose:
            model = env_purpose.strip()

    if not model:
        env_global = os.getenv("DRRD_OPENAI_MODEL")
        if env_global:
            model = env_global.strip()

    if not model:
        model = "gpt-4.1-mini"

    resolved = model
    forced = os.getenv("DRRD_FORCE_MODEL")
    if forced and forced.strip() != resolved:
        logger.warning(
            "FORCING model override: %s -> %s [purpose=%s agent=%s]",
            resolved,
            forced.strip(),
            purpose,
            agent_name,
        )
        return forced.strip()

    return resolved


@dataclass
class ChatResult:
    content: str
    raw: t.Any


def _log_request(model: str, messages: list, extra: dict):
    try:
        redacted = redact_for_logging(messages)
        preview = {
            "model": model,
            "messages": redacted,
            "extra_keys": list(extra.keys()),
        }
        logger.info("Input preview (redacted): %s", json.dumps(preview)[:1000])
    except Exception as e:
        safe_exc(logger, "", "[LLM] Could not log request preview", e)


def _log_400(e: Exception):
    safe_exc(logger, "", "[LLM] OpenAI error", e)
    try:
        if hasattr(e, "response") and hasattr(e.response, "json"):
            safe_exc(logger, "", "[LLM] Error JSON", Exception(e.response.json()))
        elif hasattr(e, "response") and hasattr(e.response, "text"):
            safe_exc(logger, "", "[LLM] Error text", Exception(e.response.text))
    except Exception as inner:
        safe_exc(logger, "", "[LLM] Could not log error body", inner)


def _validate_messages(messages: list):
    if not isinstance(messages, list) or not messages:
        raise ValueError(
            "messages must be a non-empty list of {role, content} objects."
        )
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            raise ValueError(f"messages[{i}] is not a dict.")
        if m.get("role") not in {"system", "user", "assistant", "tool"}:
            raise ValueError(f"messages[{i}].role invalid: {m.get('role')}")
        c = m.get("content")
        if c is None:
            raise ValueError(f"messages[{i}].content must be str or list (for vision).")
        if not isinstance(c, str) and not isinstance(c, list):
            c = coerce_user_content(c)
            m["content"] = c
            if not isinstance(c, str) and not isinstance(c, list):
                raise ValueError(
                    f"messages[{i}].content must be str or list (for vision)."
                )


def complete(
    system_prompt: t.Any, user_prompt: t.Any, *, model: t.Optional[str] = None, **kwargs
) -> ChatResult:
    mdl = select_model("general", model)
    messages = [
        {"role": "system", "content": coerce_user_content(system_prompt)},
        {"role": "user", "content": coerce_user_content(user_prompt)},
    ]
    _validate_messages(messages)

    scrub = dict(kwargs)
    if scrub.get("stream_options") and not scrub.get("stream"):
        scrub.pop("stream_options", None)

    _log_request(mdl, messages, scrub)

    try:
        result = call_openai(model=mdl, messages=messages, **scrub)
        resp = result["raw"]
        content = result["text"] or ""
        raw = resp.model_dump() if hasattr(resp, "model_dump") else resp
        return ChatResult(content=content, raw=raw)
    except Exception as e:
        _log_400(e)
        raise
