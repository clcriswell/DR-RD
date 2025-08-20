from __future__ import annotations

from typing import Any, Dict


class Scorecard:
    """Aggregate evaluator results into a weighted scorecard."""

    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def aggregate(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        metrics: Dict[str, Dict[str, Any]] = {}
        total_weight = 0.0
        overall = 0.0
        for name, data in results.items():
            weight = float(self.weights.get(name, 1.0))
            score = float(data.get("score", 0.0))
            metrics[name] = {
                "score": score,
                "weight": weight,
                "notes": data.get("notes", []),
            }
            overall += score * weight
            total_weight += weight
        if total_weight:
            overall /= total_weight
        return {"overall": overall, "metrics": metrics}
