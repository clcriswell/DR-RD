from __future__ import annotations

from typing import Any, Dict

from dr_rd.extensions.abcs import BaseEvaluator


class NoveltyEvaluator(BaseEvaluator):
    """Basic novelty evaluator."""

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = " ".join(str(state.get(k, "")) for k in ["results", "tasks"])
        if any(w in text.lower() for w in ["novel", "innovative", "new"]):
            return {"score": 0.8, "notes": ["novelty mentioned"]}
        return {"score": 0.5, "notes": ["novelty not demonstrated"]}
