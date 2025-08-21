from __future__ import annotations

from pathlib import Path
from typing import List

from utils.redaction import load_policy, redact_text

from core.schemas import ConceptBrief, TaskSpec

RESPONSIBILITY_TO_ROLE = {
    "research": "Research",
    "regulatory": "Regulatory",
    "finance": "Finance",
    "marketing": "Marketing Analyst",
    "cto": "CTO",
}

_POLICY = load_policy(Path(__file__).resolve().parents[1] / "config" / "redaction.yaml")


def segment_concept_brief(brief: ConceptBrief) -> List[TaskSpec]:
    tasks: List[TaskSpec] = []
    if not brief.success_metrics:
        return tasks
    for metric in brief.success_metrics:
        for responsibility, role in RESPONSIBILITY_TO_ROLE.items():
            task_text = f"{responsibility.title()} perspective on '{metric}' for {brief.problem}"
            task_text = redact_text(task_text, policy=_POLICY)
            tasks.append(TaskSpec(role=role, task=task_text))
    return tasks
