import os, json, typing as t
from dataclasses import dataclass
from openai import OpenAI
from openai import BadRequestError, APIStatusError

from dr_rd.core.prompt_utils import coerce_user_content

# Models that must use the Responses API instead of Chat Completions.
RESPONSES_ONLY = {
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o3", "o3-mini",
    "gpt-4.1-search-preview", "gpt-4o-search-preview"
}

# Models known to work with Chat Completions (not exhaustive).
CHAT_COMPAT = {
    "gpt-4o", "gpt-4o-mini", "gpt-4o-audio-preview", "gpt-3.5-turbo"
}

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

@dataclass
class ChatResult:
    content: str
    raw: dict

client = OpenAI()

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
    print(f"[LLM] OpenAI 400 Bad Request: {e}")
    # Try to dump server body if present
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
    """
    Unified completion: chooses Chat Completions or Responses based on model.
    Always sends a proper system+user message array. Returns text content.
    """
    mdl = (model or DEFAULT_MODEL).strip()

    messages = [
        {"role": "system", "content": coerce_user_content(system_prompt)},
        {"role": "user", "content": coerce_user_content(user_prompt)},
    ]
    _validate_messages(messages)

    # Defensive param scrub for Chat endpoint
    scrub = dict(kwargs)
    scrub.pop("response_format", None)  # Responses-only schemas
    if scrub.get("stream_options") and not scrub.get("stream"):
        scrub.pop("stream_options", None)

    _log_request(mdl, messages, scrub)

    try:
        if mdl in RESPONSES_ONLY:
            # Use Responses API
            resp = client.responses.create(
                model=mdl,
                input=[{"role": "system", "content": system_prompt or ""}, {"role": "user", "content": user_prompt or ""}],
                **scrub
            )
            # The Responses API returns output in a different shape
            # Extract plain text
            text_chunks = []
            for item in getattr(resp, "output", []) or []:
                if getattr(item, "type", "") == "message":
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", "") == "output_text":
                            text_chunks.append(getattr(c, "text", ""))
            content = "".join(text_chunks) if text_chunks else (getattr(resp, "output_text", None) or "")
            return ChatResult(content=content, raw=resp.model_dump() if hasattr(resp, "model_dump") else resp)
        else:
            # Default to Chat Completions
            resp = client.chat.completions.create(model=mdl, messages=messages, **scrub)
            content = resp.choices[0].message.content if resp.choices else ""
            return ChatResult(content=content, raw=resp.model_dump() if hasattr(resp, "model_dump") else resp)
    except BadRequestError as e:
        _log_400(e)
        msg = str(getattr(e, "message", e)).lower()
        if "model" in msg and mdl != "gpt-4o-mini":
            print("[LLM] Retrying with gpt-4o-mini due to model error")
            return complete(system_prompt, user_prompt, model="gpt-4o-mini", **kwargs)
        # Help the user if they picked a Responses-only model by mistake
        if mdl in RESPONSES_ONLY:
            print(f"[LLM] Model {mdl} requires the Responses API. We routed correctly. Check other parameters.")
        else:
            print(
                "[LLM] If you intend to use models like gpt-4.1 or o3*, set OPENAI_MODEL accordingly so we use Responses API."
            )
        raise
    except APIStatusError as e:
        print(f"[LLM] API status error: {e}")
        raise
