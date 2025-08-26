"""Helpers to transform trace bundles for UI visualization."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd  # type: ignore

from .schema import TraceBundle


def to_rows(bundle: TraceBundle) -> List[Dict[str, Any]]:
    """Flatten events to a list of dictionaries for tabular views."""
    rows: List[Dict[str, Any]] = []
    for ev in bundle.events:
        rows.append(
            {
                "ts": ev.ts,
                "node": ev.node,
                "phase": ev.phase,
                "task_id": ev.task_id,
                "agent": ev.agent,
                "tool": ev.tool,
                "score": ev.score,
                "attempt": ev.attempt,
                "duration_s": ev.duration_s,
                "tokens": ev.tokens,
                "cost_usd": ev.cost_usd,
            }
        )
    return rows


def to_dataframe(bundle: TraceBundle) -> pd.DataFrame:
    """Return a :class:`~pandas.DataFrame` of the bundle events."""
    return pd.DataFrame(to_rows(bundle))


def durations_series(bundle: TraceBundle) -> pd.DataFrame:
    """Return a DataFrame with timestamp, node, and duration for plotting."""
    df = to_dataframe(bundle)
    if df.empty:
        return df
    return df[["ts", "node", "duration_s"]].dropna()
