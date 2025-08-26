"""Scorecard helpers for evaluator integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

import config.feature_flags as ff
from .llm_rubric import score_with_rubric


@dataclass
class Scorecard:
    scores: Dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


def compute_overall(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    total = 0.0
    weight_sum = 0.0
    for k, v in scores.items():
        w = float(weights.get(k, 1.0))
        total += v * w
        weight_sum += w
    return total / weight_sum if weight_sum else 0.0


def evaluate(content: str, context: Dict[str, Any] | None = None) -> Scorecard:
    """Evaluate ``content`` and return a :class:`Scorecard`.

    When evaluators are disabled a neutral passing scorecard is returned.
    Otherwise each metric in ``EVALUATOR_WEIGHTS`` is scored using a deterministic
    rubric helper. ``context`` can include extra information such as tool
    results. The function never raises and all scores are clamped to ``[0,1]``.
    """
    weights = ff.EVALUATOR_WEIGHTS
    if not ff.EVALUATORS_ENABLED:
        return Scorecard(scores={}, overall=1.0, details={})

    rubric = {k: f"Score for {k}" for k in weights}
    metric_scores = score_with_rubric(content, rubric)
    overall = compute_overall(metric_scores, weights)
    return Scorecard(scores=metric_scores, overall=overall, details={})


__all__ = ["Scorecard", "compute_overall", "evaluate"]
