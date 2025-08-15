from __future__ import annotations

import dr_rd.evaluation.llm_rubric as lr
from dr_rd.extensions.abcs import BaseEvaluator


NOVELTY_RUBRIC = (
    "Assess originality vs. standard solutions for this domain. "
    "Return a single 0–1 score where 0 = derivative/common, 1 = highly novel."
)


class NoveltyEvaluator(BaseEvaluator):
    """Novelty evaluator backed by an LLM rubric."""

    def evaluate(self, workspace) -> float:  # type: ignore[override]
        text = lr.workspace_to_text(workspace)
        return lr.score_with_rubric(text, NOVELTY_RUBRIC)
