from __future__ import annotations

import json
import re
from typing import Any, Tuple


_MATERIAL_RE = re.compile(r"\bMaterial [A-Z]\b")
_JOURNAL_RE = re.compile(r"\b(?:Research )?(Journal|Study) [A-Z]\b")


def _detect_placeholder(obj: Any) -> str | None:
    if isinstance(obj, str):
        s = obj.strip()
        if s == "" or s == "Not determined":
            return "empty"
        if _MATERIAL_RE.search(s):
            return "material_name"
        if "example.com" in s:
            return "fake_url"
        if _JOURNAL_RE.search(s):
            return "generic_source"
        return None
    if isinstance(obj, list):
        for v in obj:
            reason = _detect_placeholder(v)
            if reason:
                return reason
        return None
    if isinstance(obj, dict):
        for v in obj.values():
            reason = _detect_placeholder(v)
            if reason:
                return reason
        if obj == {}:
            return "empty"
        return None
    return "empty" if obj in (None, "") else None


def evaluate(payload: Any) -> Tuple[bool, str]:
    try:
        data = payload
        if isinstance(payload, str):
            data = json.loads(payload)
    except Exception:
        data = payload
    reason = _detect_placeholder(data)
    if reason:
        return False, reason
    return True, ""


__all__ = ["evaluate"]
