from __future__ import annotations

import re
from typing import Optional

import evaluation.llm_rubric as lr
from extensions.abcs import BaseEvaluator


COST_RUBRIC = (
    "If no numeric normalized cost in [0,1] is provided, infer cost realism and affordability given scope, "
    "and return a conservative 0–1 score where higher is better (lower real cost / higher affordability). "
    "Return STRICT JSON with keys: score (float 0..1) and rationale (string)."
)


def _clip(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _extract_normalized_cost(text: str) -> Optional[float]:
    """Attempt to extract a normalized cost value from ``text``.

    Looks for patterns like ``cost: 0.2`` or ``budget is 25%`` near the keywords
    ``cost``, ``budget`` or ``price``. Dollar amounts or other numbers are
    ignored to avoid accidental conversions.
    """

    window = r"(?:[^0-9%]{0,20})"
    pat = rf"(?i)\b(cost|budget|price)\b{window}([0-9]*\.?[0-9]+)\s*(%)?"
    m = re.search(pat, text)
    if not m:
        return None
    val = float(m.group(2))
    if m.group(3):
        return _clip(val / 100.0)
    if 0.0 <= val <= 1.0:
        return val
    return None


class CostEvaluator(BaseEvaluator):
    """Cost evaluator that leverages normalized cost or an LLM rubric."""

    def evaluate(self, workspace) -> float:  # type: ignore[override]
        text = lr.workspace_to_text(workspace)
        norm = _extract_normalized_cost(text)
        if norm is not None:
            return _clip(1.0 - norm)
        return lr.score_with_rubric(text, COST_RUBRIC)


__all__ = ["CostEvaluator"]

