from __future__ import annotations

import json
from typing import Tuple, Any


def _has_placeholder(obj: Any) -> bool:
    if isinstance(obj, str):
        return obj.strip() == "" or obj.strip() == "Not determined"
    if isinstance(obj, list):
        return any(_has_placeholder(v) for v in obj)
    if isinstance(obj, dict):
        return any(_has_placeholder(v) for v in obj.values()) or obj == {}
    return obj in (None, "")


def evaluate(payload: Any) -> Tuple[bool, str]:
    try:
        data = payload
        if isinstance(payload, str):
            data = json.loads(payload)
    except Exception:
        data = payload
    if _has_placeholder(data):
        return False, "placeholder detected"
    return True, ""


__all__ = ["evaluate"]
