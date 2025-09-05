from __future__ import annotations

from typing import Any

import yaml

from core.redaction import Redactor, redact_text


def redact_dict(obj: Any, mode: str = "heavy") -> Any:
    """Recursively redact strings within *obj* using ``Redactor``."""
    redactor = Redactor()

    def _walk(o: Any):
        if isinstance(o, str):
            r, _, _ = redactor.redact(o, mode=mode)
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


__all__ = ["Redactor", "redact_text", "redact_dict", "load_policy"]
