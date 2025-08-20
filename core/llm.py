import os, json, typing as t
from dataclasses import dataclass

from core.prompt_utils import coerce_user_content
from core.llm_client import call_openai

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5").strip()


@dataclass
class ChatResult:
    content: str
    raw: t.Any


def _log_request(model: str, messages: list, extra: dict):
    try:
        preview = {
            "model": model,
            "num_messages": len(messages),
            "roles": [m.get("role") for m in messages],
            "has_system": any(m.get("role") == "system" for m in messages),
            "has_user": any(m.get("role") == "user" for m in messages),
            "extra_keys": list(extra.keys()),
        }
        print(f"[LLM] Request preview: {json.dumps(preview)[:1000]}")
    except Exception as e:
        print(f"[LLM] Could not log request preview: {e}")


def _log_400(e: Exception):
    print(f"[LLM] OpenAI error: {e}")
    try:
        if hasattr(e, "response") and hasattr(e.response, "json"):
            print(f"[LLM] Error JSON: {e.response.json()}")
        elif hasattr(e, "response") and hasattr(e.response, "text"):
            print(f"[LLM] Error text: {e.response.text}")
    except Exception as inner:
        print(f"[LLM] Could not log error body: {inner}")


def _validate_messages(messages: list):
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list of {role, content} objects.")
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


def complete(system_prompt: t.Any, user_prompt: t.Any, *, model: t.Optional[str] = None, **kwargs) -> ChatResult:
    mdl = (model or DEFAULT_MODEL).strip()
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
