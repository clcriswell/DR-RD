from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional
import json
import os
import re
import traceback
import uuid


HOME = re.escape(os.path.expanduser("~"))


@dataclass(frozen=True)
class SafeError:
    kind: str
    user_message: str
    tech_message: str
    traceback: Optional[str]
    support_id: str
    context: dict[str, Any]


KIND_MESSAGES = {
    "api": "The model endpoint did not accept the request. Try again later or change the provider.",
    "timeout": "This step exceeded the time limit. Try a smaller scope or retry.",
    "validation": "Inputs are incomplete or invalid. Check required fields.",
    "io": "A file or network resource was unavailable. Verify path or connection.",
    "unknown": "An unexpected error occurred. Please try again.",
}


def classify(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "http" in name or "api" in name:
        return "api"
    if isinstance(exc, (ValueError, KeyError, AssertionError)) or "validation" in name:
        return "validation"
    if isinstance(exc, (OSError, IOError, FileNotFoundError)) or "io" in name:
        return "io"
    return "unknown"


_RE_PATTERNS = [
    (r"sk-[A-Za-z0-9]{16,}", "[REDACTED]"),
    (r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]"),
    (r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", "[REDACTED_EMAIL]"),
    (HOME + r"[\w/._-]*", "[REDACTED_PATH]"),
    (r"api_key\s*[:=]\s*[^\s]+", "api_key=[REDACTED]"),
]


def redact(text: str) -> str:
    if not text:
        return text
    result = text
    for pattern, repl in _RE_PATTERNS:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
    return result


def make_safe_error(
    exc: Exception,
    *,
    run_id: str | None,
    phase: str | None,
    step_id: str | None,
) -> SafeError:
    kind = classify(exc)
    tech_message = redact(str(exc).strip().replace("\n", " "))
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    tb = redact(tb)
    support_id = uuid.uuid4().hex[:8]
    context: dict[str, Any] = {}
    if run_id:
        context["run_id"] = run_id
    if phase:
        context["phase"] = phase
    if step_id:
        context["step_id"] = step_id
    return SafeError(
        kind=kind,
        user_message=KIND_MESSAGES.get(kind, KIND_MESSAGES["unknown"]),
        tech_message=tech_message,
        traceback=tb or None,
        support_id=support_id,
        context=context,
    )


def as_json(safe: SafeError) -> bytes:
    return json.dumps(asdict(safe), ensure_ascii=False).encode("utf-8")

