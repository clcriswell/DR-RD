from __future__ import annotations

"""Centralised retrieval provenance tracking."""

from typing import Dict, List
import json

_TRACE: List[Dict[str, object]] = []


def record_sources(task_id: str, sources: List[Dict[str, object]]) -> None:
    """Record ``sources`` retrieved for ``task_id``."""

    for src in sources:
        entry = dict(src)
        entry["task_id"] = task_id
        _TRACE.append(entry)


def get_trace() -> List[Dict[str, object]]:
    """Return a copy of the retrieval provenance trace."""

    return list(_TRACE)


def export_jsonl(path: str) -> None:
    """Export provenance trace to ``path`` in JSON Lines format."""

    with open(path, "w", encoding="utf-8") as fh:
        for item in _TRACE:
            fh.write(json.dumps(item) + "\n")


__all__ = ["record_sources", "get_trace", "export_jsonl"]
