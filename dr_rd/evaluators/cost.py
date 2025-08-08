from __future__ import annotations

from typing import Any, Dict, List

from dr_rd.extensions.abcs import BaseEvaluator


class CostEvaluator(BaseEvaluator):
    """Naive cost evaluator.

    This stub implementation simply checks for a ``cost`` field in the
    workspace state. If present, lower costs yield higher scores. In the
    absence of explicit information it returns a neutral score.
    """

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        cost = state.get("cost") or state.get("results", {}).get("cost")
        if cost is None:
            return {"score": 0.5, "notes": ["no cost data"]}
        try:
            cost = float(cost)
        except Exception:  # pragma: no cover - defensive
            return {"score": 0.5, "notes": ["invalid cost data"]}
        # Simple heuristic: lower cost -> higher score, assuming cost in [0,1]
        score = max(0.0, min(1.0, 1.0 - cost))
        return {"score": score, "notes": []}
