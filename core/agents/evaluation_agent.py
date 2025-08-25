from __future__ import annotations

import re
from typing import Dict, List, Any, Optional

import config.feature_flags as ff
from utils.logging import logger

try:
    from evaluation import llm_rubric
except Exception:  # pragma: no cover - optional
    llm_rubric = None  # type: ignore


class EvaluationAgent:
    """Lightweight heuristic evaluator for agent outputs."""

    name = "Evaluation"

    def __init__(self, model: str | None = None):
        self.model = model or ""

    # ------------------------------------------------------------------
    def _has_placeholder(self, text: str) -> bool:
        return bool(re.search(r"(?i)\b(TBD|TODO|\?\?\?|placeholder)\b", text))

    def _score_clarity(self, texts: List[str]) -> float:
        if any(self._has_placeholder(t) for t in texts):
            return 0.2
        return 1.0

    def _score_completeness(self, answers: Dict[str, str], payloads: Dict[str, dict]) -> float:
        if not answers:
            return 0.0
        penalties = 0.0
        total_roles = len(answers)
        for role, ans in answers.items():
            if not ans.strip():
                penalties += 1.0
                continue
            if self._has_placeholder(ans):
                penalties += 0.5
            payload = payloads.get(role) or {}
            for key in ("findings", "risks", "next_steps"):
                if key in payload and not payload.get(key):
                    penalties += 0.2
        score = max(0.0, 1.0 - penalties / max(1, total_roles))
        return min(1.0, score)

    def _score_grounding(self, answers: Dict[str, str], payloads: Dict[str, dict], context: Dict[str, Any]) -> float:
        rag = bool(context.get("rag_enabled")) or bool(context.get("live_search_enabled"))
        if not rag:
            return 1.0
        cites = 0
        for role, ans in answers.items():
            if re.search(r"\[(?:\d+|[a-z])\]", ans) or "according to" in ans.lower():
                cites += 1
            payload = payloads.get(role) or {}
            cites += len(payload.get("citations", []) or [])
            if re.search(r"https?://", ans):
                cites += 1
        if cites == 0:
            return 0.0
        return 1.0 if cites >= 2 else 0.5

    # ------------------------------------------------------------------
    def run(
        self,
        idea: str,
        answers_by_role: Dict[str, str],
        payload_by_role: Dict[str, dict],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = context or {}
        texts = list(answers_by_role.values())
        clarity = self._score_clarity(texts)
        completeness = self._score_completeness(answers_by_role, payload_by_role)
        grounding = self._score_grounding(answers_by_role, payload_by_role, context)
        weights = ff.EVAL_WEIGHTS
        overall = (
            clarity * weights.get("clarity", 0.0)
            + completeness * weights.get("completeness", 0.0)
            + grounding * weights.get("grounding", 0.0)
        )
        overall = round(overall, 4)

        if ff.EVALUATION_USE_LLM_RUBRIC and llm_rubric is not None:
            try:
                text = "\n\n".join(texts)
                rubric = "Clarity, Completeness, Grounding"
                overall = llm_rubric.score_with_rubric(text, rubric)
            except Exception as e:  # pragma: no cover
                logger.warning("LLM rubric scoring failed: %s", e)

        insufficient = overall < ff.EVAL_MIN_OVERALL
        findings: List[str] = []
        followups: List[Dict[str, str]] = []
        if insufficient:
            if clarity < 0.7:
                followups.append(
                    {
                        "role": "Research Scientist",
                        "title": "Improve clarity",
                        "description": "Polish language and remove placeholders.",
                    }
                )
                findings.append("low clarity")
            if completeness < 0.7:
                followups.append(
                    {
                        "role": "Planner",
                        "title": "Patch Plan for Gaps",
                        "description": "Add tasks addressing missing findings or sections.",
                    }
                )
                findings.append("incomplete outputs")
            if grounding < 0.7:
                followups.append(
                    {
                        "role": "Research Scientist",
                        "title": "Add citations",
                        "description": "Provide at least two diverse citations.",
                    }
                )
                findings.append("weak grounding")
        followups = followups[:3]

        metrics = {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
        for payload in payload_by_role.values():
            if isinstance(payload, dict):
                metrics["tokens_in"] += int(payload.get("tokens_in", 0) or 0)
                metrics["tokens_out"] += int(payload.get("tokens_out", 0) or 0)
                try:
                    metrics["cost_usd"] += float(payload.get("cost", 0.0) or 0.0)
                except Exception:
                    pass

        return {
            "score": {
                "clarity": clarity,
                "completeness": completeness,
                "grounding": grounding,
                "overall": overall,
            },
            "insufficient": insufficient,
            "findings": findings,
            "followups": followups,
            "notes": "heuristic",
            "metrics": metrics,
        }

