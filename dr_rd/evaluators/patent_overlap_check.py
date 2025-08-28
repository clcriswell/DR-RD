from __future__ import annotations

from typing import Tuple


def evaluate(payload: dict, min_families: int = 1) -> Tuple[bool, str]:
    records = payload.get("records", [])
    pubs = set()
    families = set()
    for rec in records:
        pub = rec.get("pub_number")
        if pub in pubs:
            return False, "duplicate publication"
        pubs.add(pub)
        for code in rec.get("cpc_codes", []) + rec.get("ipc_codes", []):
            families.add(code.split("/")[0])
    if len(families) < min_families:
        return False, "insufficient diversity"
    return True, ""


__all__ = ["evaluate"]
