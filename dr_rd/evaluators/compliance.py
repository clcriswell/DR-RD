from __future__ import annotations

from typing import Any, Dict

from dr_rd.extensions.abcs import BaseEvaluator


class ComplianceEvaluator(BaseEvaluator):
    """Simple compliance evaluator."""

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = " ".join(str(state.get(k, "")) for k in ["results", "tasks"])
        if "compliance" in text.lower() or "regulation" in text.lower():
            return {"score": 0.8, "notes": ["compliance considered"]}
        return {"score": 0.5, "notes": ["compliance not addressed"]}
