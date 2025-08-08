from __future__ import annotations

from typing import Any, Dict

from dr_rd.extensions.abcs import BaseEvaluator


class FeasibilityEvaluator(BaseEvaluator):
    """Crude feasibility evaluator."""

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = " ".join(str(state.get(k, "")) for k in ["results", "tasks"])
        if "feasible" in text.lower():
            return {"score": 0.8, "notes": ["feasibility addressed"]}
        return {"score": 0.5, "notes": ["feasibility unclear"]}
