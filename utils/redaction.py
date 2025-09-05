from __future__ import annotations

import re
from typing import Any

import yaml

from core.redaction import Redactor

_PLACEHOLDER_RE = re.compile(r"\[(SECRET|EMAIL|PHONE|IPV4|IPV6|IP|ADDRESS|PERSON|ORG|DEVICE)_\d+\]")
REDACTION_TOKEN = "•••"


def _strip_placeholders(text: str) -> str:
    """Replace redaction placeholders with a fixed token."""
    return _PLACEHOLDER_RE.sub(REDACTION_TOKEN, text)


def redact_text(text: str, mode: str = "heavy", role: str | None = None) -> str:
    """Return *text* with sensitive values replaced by ``REDACTION_TOKEN``."""

    redacted, _, _ = Redactor().redact(text, mode=mode, role=role)
    return _strip_placeholders(redacted)


def redact_dict(obj: Any, max_len: int | None = None, mode: str = "heavy") -> Any:
    """Recursively redact strings within *obj* using ``Redactor``.

    ``max_len`` limits the length of resulting strings. When specified, any
    redacted string longer than this value will be truncated and suffixed with
    an ellipsis.
    """

    redactor = Redactor()

    def _walk(o: Any):
        if isinstance(o, str):
            r, _, _ = redactor.redact(o, mode=mode)
            r = _strip_placeholders(r)
            if max_len is not None and len(r) > max_len:
                return r[:max_len] + "…"
            return r
        if isinstance(o, list):
            return [_walk(v) for v in o]
        if isinstance(o, dict):
            return {k: _walk(v) for k, v in o.items()}
        return o

    return _walk(obj)


def load_policy(path_or_dict: Any) -> dict:
    """Compatibility shim; return YAML mapping if *path_or_dict* is a path."""
    if isinstance(path_or_dict, dict):
        return path_or_dict
    with open(path_or_dict, encoding="utf-8") as f:  # pragma: no cover - legacy
        return yaml.safe_load(f) or {}


def redact_public(text: str) -> str:
    """Return text safe for public sharing."""

    return redact_text(text, mode="heavy")


__all__ = [
    "Redactor",
    "redact_text",
    "redact_dict",
    "load_policy",
    "redact_public",
]
