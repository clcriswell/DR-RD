from __future__ import annotations

import os
import random
from typing import Callable, Dict, Tuple, Any

from .design_space import DesignSpace


def optimize(
    design: Dict[str, Any],
    design_space: DesignSpace,
    objective_fn: Callable[[Dict[str, Any], Dict[str, Any]], float],
    simulator: Callable[[Dict[str, Any]], Dict[str, Any]],
    *,
    strategy: str = "random",
    max_evals: int = 50,
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

    best_design = None
    best_metrics = None
    best_score = float("-inf")

    def evaluate(candidate: Dict[str, Any]):
        nonlocal best_design, best_metrics, best_score
        metrics = simulator(candidate)
        score = objective_fn(candidate, metrics)
        if score > best_score:
            best_design, best_metrics, best_score = candidate, metrics, score

    if design:
        evaluate(design)

    if strategy == "grid":
        for candidate in design_space.iter_grid():
            evaluate(candidate)
    else:
        for _ in range(max_evals):
            candidate = design_space.sample()
            evaluate(candidate)

    return best_design, best_metrics
