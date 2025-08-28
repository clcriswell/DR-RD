"""Utilities for diffing provenance runs."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .trace_models import RunMeta, Span


def load_run(path: str | Path) -> Tuple[RunMeta, List[Span]]:
    """Load run metadata and spans from ``path``."""
    base = Path(path)
    meta = RunMeta(**json.loads((base / "run_meta.json").read_text()))
    spans: List[Span] = []
    prov = base / "provenance.jsonl"
    if prov.exists():
        for line in prov.read_text().splitlines():
            if not line.strip():
                continue
            spans.append(Span(**json.loads(line)))
    return meta, spans


def _index_by_id(spans: List[Span]) -> Dict[str, Span]:
    return {s.id: s for s in spans}


def classify_change(span_base: Span, span_cand: Span, slack_ms: int) -> Dict[str, Any]:
    """Return a dict describing changes between two spans."""
    delta = (span_cand.duration_ms or 0) - (span_base.duration_ms or 0)
    return {
        "id": span_cand.id,
        "duration_delta": delta,
        "regression": delta > slack_ms,
    }


def diff_runs(base: Tuple[RunMeta, List[Span]], cand: Tuple[RunMeta, List[Span]], *, slack_ms: int = 100) -> Dict[str, Any]:
    base_meta, base_spans = base
    cand_meta, cand_spans = cand
    base_idx = _index_by_id(base_spans)
    cand_idx = _index_by_id(cand_spans)

    spans_added = [asdict(s) for i, s in cand_idx.items() if i not in base_idx]
    spans_removed = [asdict(s) for i, s in base_idx.items() if i not in cand_idx]
    spans_changed: List[Dict[str, Any]] = []
    for i in set(base_idx) & set(cand_idx):
        b = base_idx[i]
        c = cand_idx[i]
        if (b.duration_ms != c.duration_ms) or (b.ok != c.ok):
            spans_changed.append(classify_change(b, c, slack_ms))

    total_latency_base = sum(s.duration_ms or 0 for s in base_spans)
    total_latency_cand = sum(s.duration_ms or 0 for s in cand_spans)
    latency_delta = total_latency_cand - total_latency_base

    failure_base = sum(1 for s in base_spans if not s.ok)
    failure_cand = sum(1 for s in cand_spans if not s.ok)
    rate_base = failure_base / max(len(base_spans), 1)
    rate_cand = failure_cand / max(len(cand_spans), 1)

    diff = {
        "spans_added": spans_added,
        "spans_removed": spans_removed,
        "spans_changed": spans_changed,
        "latency_delta_ms_total": latency_delta,
        "mean_agent_latency_delta": latency_delta / max(len(cand_spans), 1),
        "tool_failure_rate": {
            "base": rate_base,
            "cand": rate_cand,
            "delta": rate_cand - rate_base,
        },
        "model_usage_changes": {
            "base": base_meta.models,
            "cand": cand_meta.models,
        },
        "retrieval_level_changes": {
            "base": base_meta.flags.get("RETRIEVAL_LEVEL"),
            "cand": cand_meta.flags.get("RETRIEVAL_LEVEL"),
        },
    }
    return diff


__all__ = ["load_run", "diff_runs", "classify_change"]
