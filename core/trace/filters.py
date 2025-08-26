from __future__ import annotations

"""Filtering helpers for :mod:`core.trace`.

The real application exposes a rich set of filters.  For tests we implement a
minimal subset that operates on :class:`TraceBundle` objects.
"""

from collections import defaultdict
from typing import Iterable, Literal, Dict, Optional, Tuple

from .schema import TraceBundle, TraceEvent


def apply_filters(
    bundle: TraceBundle,
    by_task: Optional[Iterable[str]] = None,
    by_agent: Optional[Iterable[str]] = None,
    by_tool: Optional[Iterable[str]] = None,
    retries_only: bool = False,
    ts_range: Optional[Tuple[float, float]] = None,
) -> TraceBundle:
    """Return a new bundle filtered according to the supplied options."""

    tasks = set(by_task or [])
    agents = set(by_agent or [])
    tools = set(by_tool or [])
    start, end = (ts_range or (None, None))

    events = []
    for ev in bundle.events:
        if tasks and ev.task_id not in tasks:
            continue
        if agents and ev.agent not in agents:
            continue
        if tools and ev.tool not in tools:
            continue
        if retries_only and (ev.attempt or 1) <= 1:
            continue
        if start is not None and ev.ts < start:
            continue
        if end is not None and ev.ts > end:
            continue
        events.append(ev)
    return TraceBundle(events=events)


def group_stats(bundle: TraceBundle, group_by: Literal["task", "agent", "tool"]) -> Dict[str, Dict[str, float]]:
    """Aggregate basic stats for ``bundle`` grouped by ``group_by`` field."""

    out: Dict[str, Dict[str, float]] = defaultdict(lambda: {
        "count": 0,
        "duration_s": 0.0,
        "tokens": 0,
        "cost_usd": 0.0,
    })

    for ev in bundle.events:
        key = getattr(ev, {
            "task": "task_id",
            "agent": "agent",
            "tool": "tool",
        }[group_by])
        if key is None:
            key = "unknown"
        stats = out[key]
        stats["count"] += 1
        stats["duration_s"] += ev.duration_s or 0.0
        stats["tokens"] += ev.tokens or 0
        stats["cost_usd"] += ev.cost_usd or 0.0
    return dict(out)
