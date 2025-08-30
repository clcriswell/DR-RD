from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import yaml

TOKEN_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"Bearer\s+[A-Za-z0-9._-]{10,}",
]

PII_PATTERNS = [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b\+?\d[\d \-()]{7,}\d\b",
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:\d[ -]*?){13,19}\b",
]

_COMPILED = [re.compile(p) for p in TOKEN_PATTERNS + PII_PATTERNS]


def _regex_redact(s: str, mask: str = "•••") -> str:
    for rx in _COMPILED:
        s = rx.sub(mask, s)
    return s


def redact_text(
    arg1: Any,
    arg2: str | None = None,
    mask: str = "•••",
    *,
    policy: Mapping[str, Any] | None = None,
) -> str:
    """Redact tokens/PII or apply a legacy policy.

    This function supports two call styles for backward compatibility:
    ``redact_text("secret")`` for regex-based redaction and
    ``redact_text(policy, text)`` for the older policy-based interface.
    """
    if isinstance(arg1, Mapping) or policy is not None:
        if policy is None:
            policy = arg1  # type: ignore[assignment]
            text = arg2 or ""
        else:
            text = str(arg1)
        result = text
        for name, cfg in policy.items():
            if not cfg.get("enabled", True):
                continue
            pattern = cfg.get("pattern")
            token = cfg.get("token", f"[REDACTED:{name.upper()}]")
            if not pattern:
                continue
            result = re.sub(pattern, token, result, flags=re.IGNORECASE)
        return result
    text = str(arg1)
    return _regex_redact(text, mask)


def redact_dict(obj: Any, mask: str = "•••", max_len: int = 2000) -> Any:
    """Walk mappings/lists, redact strings, and clamp long values."""
    if isinstance(obj, Mapping):
        return {k: redact_dict(v, mask, max_len) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_dict(v, mask, max_len) for v in obj]
    if isinstance(obj, str):
        s = _regex_redact(obj, mask)
        if len(s) > max_len:
            return s[:max_len] + "\u2026"
        return s
    return obj


# Legacy helpers -----------------------------------------------------------


def load_policy(path_or_dict: Any) -> dict[str, Any]:
    if isinstance(path_or_dict, dict):
        return path_or_dict
    path = Path(path_or_dict)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data
