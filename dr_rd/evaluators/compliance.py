from __future__ import annotations

import evaluation.llm_rubric as lr
from extensions.abcs import BaseEvaluator

COMPLIANCE_RUBRIC = (
    "Assess privacy posture, adherence to platform Terms of Service, "
    "and regulatory fit (e.g., GDPR/CCPA/COPPA as relevant). "
    "Return 0–1 where 0 = non‑compliant, 1 = strongly compliant."
)


class ComplianceEvaluator(BaseEvaluator):
    """Compliance evaluator backed by an LLM rubric."""

    def evaluate(self, workspace) -> float:  # type: ignore[override]
        text = lr.workspace_to_text(workspace)
        return lr.score_with_rubric(text, COMPLIANCE_RUBRIC)
