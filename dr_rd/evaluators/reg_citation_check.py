from __future__ import annotations

from typing import Any, Tuple


def evaluate(payload: dict) -> Tuple[bool, str]:
    records = payload.get("records", [])
    for rec in records:
        src = rec.get("source")
        if not src or not src.get("id") or not src.get("url"):
            return False, "missing source"
        if not rec.get("cfr_refs"):
            return False, "missing cfr_refs"
    return True, ""


__all__ = ["evaluate"]
