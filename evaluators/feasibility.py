from __future__ import annotations

import evaluation.llm_rubric as lr
from extensions.abcs import BaseEvaluator


FEASIBILITY_RUBRIC = (
    "Assess realism of resources, time, dependencies, and risk mitigations. "
    "Return a single 0–1 score where 0 = not feasible, 1 = highly feasible."
)


class FeasibilityEvaluator(BaseEvaluator):
    """Feasibility evaluator backed by an LLM rubric."""

    def evaluate(self, workspace) -> float:  # type: ignore[override]
        text = lr.workspace_to_text(workspace)
        return lr.score_with_rubric(text, FEASIBILITY_RUBRIC)
