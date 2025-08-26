"""Utilities for summarizing simulation runs."""
from __future__ import annotations

import math
from statistics import mean, median, pstdev
from typing import Dict, List, Any, Optional


def summarize_runs(runs: List[Dict[str, Any]], max_points: Optional[int] = None) -> Dict[str, Any]:
    """Compute basic statistics and detect sweep key.

    If ``max_points`` is provided and the number of runs exceeds it, the
    returned dictionary will include ``downsampled`` = True and ``sampled``
    with a subset of runs for plotting.
    """

    summary: Dict[str, Any] = {"count": len(runs)}
    if not runs:
        summary.update({"sweep_key": None, "mean": 0.0, "median": 0.0, "std": 0.0})
        return summary

    keys = set().union(*(r.keys() for r in runs)) - {"output"}
    varying = [k for k in keys if len({r.get(k) for r in runs}) > 1]
    summary["sweep_key"] = varying[0] if len(varying) == 1 else None

    outputs = [float(r.get("output", 0.0)) for r in runs]
    summary["mean"] = mean(outputs)
    summary["median"] = median(outputs)
    summary["std"] = pstdev(outputs) if len(outputs) > 1 else 0.0

    sorted_out = sorted(outputs)

    def _percentile(p: float) -> float:
        if not sorted_out:
            return 0.0
        k = (len(sorted_out) - 1) * p / 100.0
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_out[int(k)]
        return sorted_out[f] + (sorted_out[c] - sorted_out[f]) * (k - f)

    summary["p5"] = _percentile(5)
    summary["p50"] = _percentile(50)
    summary["p95"] = _percentile(95)

    if max_points and len(runs) > max_points:
        step = len(runs) / max_points
        idxs = [int(i * step) for i in range(max_points)]
        summary["sampled"] = [runs[i] for i in idxs]
        summary["downsampled"] = True
    else:
        summary["sampled"] = runs
        summary["downsampled"] = False
    return summary
