from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .redaction import redact_text


@dataclass(frozen=True)
class SafeError:
    kind: str
    user_message: str
    tech_message: str
    traceback: str | None
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


def classify_provider_error(exc: Exception) -> str:
    """Map provider SDK exceptions to canonical kinds."""
    name = exc.__class__.__name__.lower()
    msg = str(exc).lower()
    if "rate" in name or "rate" in msg and "limit" in msg:
        return "rate_limit"
    if "timeout" in name or "timed" in msg:
        return "timeout"
    if "auth" in name or "unauthorized" in msg or "api key" in msg:
        return "auth"
    if "quota" in name or "billing" in msg:
        return "quota"
    if isinstance(exc, (ValueError, KeyError, TypeError)) or "validation" in name:
        return "validation"
    return "transient"


MAX_CHARS = 2000


def make_safe_error(
    exc: Exception,
    *,
    run_id: str | None,
    phase: str | None,
    step_id: str | None,
) -> SafeError:
    kind = classify(exc)
    tech_message = redact_text(str(exc).strip().replace("\n", " "))[:MAX_CHARS]
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    tb = redact_text(tb)[:MAX_CHARS]
    support_id = uuid.uuid4().hex[:8]
    context: dict[str, Any] = {}
    if run_id:
        context["run_id"] = run_id
    if phase:
        context["phase"] = phase
    if step_id:
        context["step_id"] = step_id
    safe = SafeError(
        kind=kind,
        user_message=KIND_MESSAGES.get(kind, KIND_MESSAGES["unknown"]),
        tech_message=tech_message,
        traceback=tb or None,
        support_id=support_id,
        context=context,
    )
    try:
        from utils.otel import current_ids

        ids = current_ids()
        if ids:
            safe.context["trace_id"] = ids.get("trace_id")
            safe.context["span_id"] = ids.get("span_id")
    except Exception:
        pass
    return safe


def redact(text: str) -> str:
    """Back-compat wrapper for redaction."""
    return redact_text(text)


def _coerce_sets(obj: Any) -> Any:
    """Recursively convert sets to sorted lists for JSON serialization."""

    if isinstance(obj, set):
        # Sort deterministically using string representation to avoid type
        # comparison issues between heterogeneous elements.
        return sorted((_coerce_sets(v) for v in obj), key=lambda x: str(x))
    if isinstance(obj, dict):
        return {k: _coerce_sets(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce_sets(v) for v in obj]
    return obj


def as_json(safe: SafeError) -> bytes:
    data = _coerce_sets(asdict(safe))
    return json.dumps(data, ensure_ascii=False).encode("utf-8")
