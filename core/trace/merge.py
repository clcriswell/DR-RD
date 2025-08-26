"""Utilities for merging disparate trace sources."""
from __future__ import annotations

from typing import Dict, List, Optional, Iterable, Any

from .schema import TraceBundle, TraceEvent


_FIELDS = {
    "ts",
    "timestamp",
    "node",
    "phase",
    "task_id",
    "agent",
    "tool",
    "score",
    "attempt",
    "duration",
    "duration_s",
    "tokens",
    "cost_usd",
    "cost",
}


def _scrub(value: Any) -> Any:
    if isinstance(value, str) and any(k in value.lower() for k in ["token", "secret", "key"]):
        return "[REDACTED]"
    return value


def _normalize(evt: Dict[str, Any], source: str) -> TraceEvent:
    ts = float(evt.get("ts") or evt.get("timestamp") or 0.0)
    node = str(evt.get("node") or evt.get("name") or source)
    phase = str(evt.get("phase") or evt.get("event") or source)
    meta = {k: _scrub(v) for k, v in evt.items() if k not in _FIELDS}
    return TraceEvent(
        ts=ts,
        node=node,
        phase=phase,
        task_id=evt.get("task_id"),
        agent=evt.get("agent"),
        tool=evt.get("tool"),
        score=evt.get("score"),
        attempt=evt.get("attempt"),
        duration_s=evt.get("duration_s") or evt.get("duration"),
        tokens=evt.get("tokens"),
        cost_usd=evt.get("cost_usd") or evt.get("cost"),
        meta=meta,
    )


def merge_traces(
    graph_trace: Optional[Iterable[Dict[str, Any]]],
    tool_trace: Optional[Iterable[Dict[str, Any]]],
    retrieval_trace: Optional[Iterable[Dict[str, Any]]],
    autogen_trace: Optional[Iterable[Dict[str, Any]]] = None,
) -> TraceBundle:
    """Merge multiple trace lists into a unified, time-sorted bundle."""

    events: List[TraceEvent] = []
    for source, trace in [
        ("graph", graph_trace),
        ("tool", tool_trace),
        ("retrieval", retrieval_trace),
        ("autogen", autogen_trace),
    ]:
        if not trace:
            continue
        for evt in trace:
            events.append(_normalize(evt, source))
    events.sort(key=lambda e: e.ts)
    return TraceBundle(events=events)


def summarize(bundle: TraceBundle) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Aggregate totals by task, agent, and tool."""

    out: Dict[str, Dict[str, Dict[str, float]]] = {
        "task": {},
        "agent": {},
        "tool": {},
    }
    for ev in bundle.events:
        for kind, key in (("task", ev.task_id), ("agent", ev.agent), ("tool", ev.tool)):
            if not key:
                continue
            entry = out[kind].setdefault(
                key, {"duration_s": 0.0, "tokens": 0.0, "cost_usd": 0.0, "count": 0}
            )
            entry["duration_s"] += ev.duration_s or 0.0
            entry["tokens"] += ev.tokens or 0
            entry["cost_usd"] += ev.cost_usd or 0.0
            entry["count"] += 1
    return out
