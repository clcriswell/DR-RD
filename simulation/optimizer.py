from __future__ import annotations

import logging
import os
import random
from typing import Callable, Dict, Tuple, Any, Optional
from .registry import register

from config.feature_flags import EVALUATORS_ENABLED
from .design_space import DesignSpace


def optimize(
    design: Dict[str, Any],
    design_space: DesignSpace,
    objective_fn: Callable[[Dict[str, Any], Dict[str, Any]], float],
    simulator: Callable[[Dict[str, Any]], Dict[str, Any]],
    *,
    strategy: str = "random",
    max_evals: int = 50,
    scorecard: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Search for the best design within ``design_space``.

    Args:
        design: Initial design to evaluate. May be empty.
        design_space: Space of parameters to explore.
        objective_fn: Function returning a scalar score given ``(design, metrics)``.
        simulator: Function mapping a design to simulation metrics.
        strategy: ``"grid"`` to exhaustively enumerate all discrete options,
            otherwise random search is performed.
        max_evals: Maximum number of random evaluations.
    Returns:
        Tuple of ``(best_design, best_metrics)`` discovered.
    """

    seed = os.getenv("RANDOM_SEED")
    if seed is not None:
        random.seed(int(seed))

    logger = logging.getLogger(__name__)

    best_design = None
    best_metrics = None
    best_score = float("-inf")
    best_idx = -1
    trial = 0

    def _summarize(d: Dict[str, Any], limit: int = 3) -> str:
        items = list(d.items())[:limit]
        return ", ".join(f"{k}={v}" for k, v in items)

    def evaluate(candidate: Dict[str, Any]):
        nonlocal best_design, best_metrics, best_score, best_idx, trial
        trial += 1
        metrics = simulator(candidate)
        score = objective_fn(candidate, metrics)
        if EVALUATORS_ENABLED and scorecard and "overall" in scorecard:
            alpha = float(os.getenv("SIM_OBJECTIVE_ALPHA", "0.7"))
            score = alpha * score + (1 - alpha) * float(scorecard.get("overall", 0.0))
        logger.info(
            "trial %d: params=%s metrics=%s score=%.3f",
            trial,
            design_space.summarize(candidate),
            _summarize(metrics),
            score,
        )
        if score > best_score:
            best_design, best_metrics, best_score, best_idx = candidate, metrics, score, trial

    if design:
        evaluate(design)

    if strategy == "grid":
        for candidate in design_space.iter_grid():
            evaluate(candidate)
    else:
        for _ in range(max_evals):
            candidate = design_space.sample()
            evaluate(candidate)

    if best_design is not None:
        logger.info(
            "best: idx=%d params=%s metrics=%s score=%.3f",
            best_idx,
            design_space.summarize(best_design),
            _summarize(best_metrics),
            best_score,
        )

    return best_design, best_metrics


@register("product_mock")
def product_mock(inputs: Dict[str, Any]):
    """Deterministic mock that multiplies ``a`` and ``b``."""
    a = float(inputs.get("a", 1))
    b = float(inputs.get("b", 1))
    obs = {"product": a * b}
    meta = {"cost_estimate_usd": 0.0, "seconds": 0.0, "backend": "mock"}
    return obs, meta
