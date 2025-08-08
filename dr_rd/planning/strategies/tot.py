"""Tree-of-thoughts style planner strategy.

This strategy generates multiple candidate plans, evaluates them and expands
the best ones for a fixed depth using a simple beam-search procedure.  The
final task list mirrors the structure produced by the existing planner so it
can be swapped in transparently when ``TOT_PLANNING_ENABLED`` is set.

The scoring mechanism prefers plans that clarify requirements when they are
missing, discuss feasibility, and explore novel angles.  If evaluator
extensions are registered and enabled, their scores are used instead of the
internal heuristic.
"""

from __future__ import annotations

from typing import Any, Dict, List
import logging

from config.feature_flags import (
    EVALUATORS_ENABLED,
    TOT_BEAM,
    TOT_K,
    TOT_MAX_DEPTH,
)
from dr_rd.extensions.abcs import BasePlannerStrategy
from dr_rd.extensions.registry import EvaluatorRegistry, PlannerStrategyRegistry

if EVALUATORS_ENABLED:
    from dr_rd import evaluators  # noqa: F401


logger = logging.getLogger(__name__)


class ToTPlannerStrategy(BasePlannerStrategy):
    """Simple beam-search tree-of-thoughts planner."""

    def __init__(self, k: int = TOT_K, beam: int = TOT_BEAM, max_depth: int = TOT_MAX_DEPTH) -> None:
        self.k = k
        self.beam = beam
        self.max_depth = max_depth

    # ----- public API --------------------------------------------------
    def plan(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of tasks derived from the best-scoring plan."""

        idea = state.get("idea")
        if not idea:  # Graceful degradation if no context is supplied
            return state.get("tasks", []) or []

        # Initial candidate generation
        candidates = []
        for tasks in self._expand([], 0, state):
            score = self._score(tasks, state)
            candidates.append({"tasks": tasks, "score": score})
        logger.info("depth 0: %s", [(i, round(c["score"], 2)) for i, c in enumerate(candidates)])

        depth = 1
        while depth <= self.max_depth and candidates:
            # Select the best beams and expand
            candidates.sort(key=lambda c: c["score"], reverse=True)
            top = candidates[: self.beam]
            new_candidates = []
            for cand in top:
                for tasks in self._expand(cand["tasks"], depth, state):
                    score = self._score(tasks, state)
                    new_candidates.append({"tasks": tasks, "score": score})
            if not new_candidates:  # no further branching possible
                break
            logger.info(
                "depth %d: %s",
                depth,
                [(i, round(c["score"], 2)) for i, c in enumerate(new_candidates)],
            )
            candidates = new_candidates
            depth += 1

        # Return tasks from the best candidate
        best = max(candidates, key=lambda c: c["score"])
        return best["tasks"]

    # ----- helpers -----------------------------------------------------
    def _expand(
        self, current: List[Dict[str, Any]], depth: int, state: Dict[str, Any]
    ) -> List[List[Dict[str, Any]]]:
        """Generate new plan branches for the given depth."""

        if depth == 0:
            options = [
                {"role": "AI R&D Coordinator", "task": "Clarify requirements with stakeholders"},
                {"role": "AI R&D Coordinator", "task": "Assess feasibility of core technologies"},
                {"role": "AI R&D Coordinator", "task": "Survey prior art and existing solutions"},
            ]
        else:
            options = [
                {
                    "role": "Systems Integration & Validation Engineer",
                    "task": "Prototype critical subsystems",
                },
                {
                    "role": "Data Scientist / Analytics Engineer",
                    "task": "Validate performance against requirements",
                },
                {
                    "role": "Project Manager / Principal Investigator",
                    "task": "Review project milestones",
                },
            ]

        branches = []
        for opt in options[: self.k]:
            branches.append(current + [opt])
        return branches

    def _score(self, tasks: List[Dict[str, Any]], state: Dict[str, Any]) -> float:
        """Score a candidate plan."""

        if EVALUATORS_ENABLED and EvaluatorRegistry.list():
            score = 0.0
            for name in EvaluatorRegistry.list():
                eval_cls = EvaluatorRegistry.get(name)
                try:
                    evaluator = eval_cls()
                    data = evaluator.evaluate({"tasks": tasks, **state})
                    score += float(data.get("score", 0.0)) * evaluator.weight()
                except Exception:  # pragma: no cover - defensive
                    continue
            return score

        # Lightweight heuristic: favour plans that clarify requirements when
        # none are provided, mention feasibility, or explore novelty.
        text = " ".join(t["task"].lower() for t in tasks)
        score = 0.1 * len(tasks)  # slight preference for more detailed plans
        if not state.get("requirements") and "clarify" in text:
            score += 2.0
        if "feasibility" in text or "feasible" in text:
            score += 1.0
        if any(word in text for word in ["novel", "survey", "prior art"]):
            score += 1.0
        requirements = state.get("requirements") or []
        for req in requirements:
            if req.lower() in text:
                score += 1.0
        return score


# Register the strategy so it can be discovered via the registry when the
# feature flag is enabled.
PlannerStrategyRegistry.register("tot", ToTPlannerStrategy)

