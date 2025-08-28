"""Summaries for safety redactions."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Any

from core.trace_models import Span


def summarize_redactions(spans: Iterable[Span]) -> Dict[str, Any]:
    counts = defaultdict(int)
    examples = defaultdict(list)
    first_seen = None
    for s in spans:
        meta = s.meta or {}
        smeta = meta.get("safety_meta", {})
        red = smeta.get("redactions_by_type", {})
        for k, v in red.items():
            counts[k] += int(v)
        ex = smeta.get("examples", {})
        for k, vals in ex.items():
            examples[k].extend(vals)
        if red and first_seen is None:
            first_seen = s.t_start
    return {
        "counts_by_type": dict(counts),
        "examples_by_type": {k: list(v) for k, v in examples.items()},
        "first_seen_at": first_seen,
    }


def propose_overrides(counts: Dict[str, int], policies: Dict[str, Any]) -> List[str]:
    suggestions: List[str] = []
    for k, v in counts.items():
        if v and k in policies.get("benign", {}):
            suggestions.append(policies["benign"][k])
    return suggestions


__all__ = ["summarize_redactions", "propose_overrides"]
