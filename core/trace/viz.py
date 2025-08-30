"""Helpers to transform trace bundles for UI visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from utils.lazy_import import lazy

from .schema import TraceBundle

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

_pd = lazy("pandas")


def to_rows(bundle: TraceBundle) -> list[dict[str, Any]]:
    """Flatten events to a list of dictionaries for tabular views."""
    rows: list[dict[str, Any]] = []
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
    return _pd.DataFrame(to_rows(bundle))


def durations_series(bundle: TraceBundle) -> pd.DataFrame:
    """Return a DataFrame with timestamp, node, and duration for plotting."""
    df = to_dataframe(bundle)
    if df.empty:
        return df
    return df[["ts", "node", "duration_s"]].dropna()
