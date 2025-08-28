from __future__ import annotations

from typing import Dict, List, Any


def evaluate(payload: Dict[str, Any]) -> bool:
    retrieval = payload.get("retrieval", {}).get("enabled")
    sources: List[Dict[str, Any]] = payload.get("sources", [])
    if retrieval and not sources:
        return False
    source_ids = {s.get("id") for s in sources}
    for ev in payload.get("evidence", []):
        if ev.get("source_id") and ev.get("source_id") not in source_ids:
            return False
    return True
