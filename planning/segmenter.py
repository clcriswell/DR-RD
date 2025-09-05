from __future__ import annotations

from typing import Dict, List

from core.redaction import Redactor
from core.schemas import ConceptBrief, TaskSpec

RESPONSIBILITY_TO_ROLE = {
    "research": "Research",
    "regulatory": "Regulatory",
    "finance": "Finance",
    "marketing": "Marketing Analyst",
    "cto": "CTO",
}


def segment_concept_brief(brief: ConceptBrief) -> List[TaskSpec]:
    redactor = Redactor()
    tasks: List[TaskSpec] = []
    if not brief.success_metrics:
        return tasks
    for metric in brief.success_metrics:
        for responsibility, role in RESPONSIBILITY_TO_ROLE.items():
            task_text = f"{responsibility.title()} perspective on '{metric}' for {brief.problem}"
            task_text, _, _ = redactor.redact(task_text, mode="light")
            tasks.append(TaskSpec(role=role, task=task_text))
    return tasks
