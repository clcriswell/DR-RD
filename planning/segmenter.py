from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import os

from utils.redaction import load_policy as _load_policy, redact_text as _redact

from core.schemas import ConceptBrief, TaskSpec

RESPONSIBILITY_TO_ROLE = {
    "research": "Research",
    "regulatory": "Regulatory",
    "finance": "Finance",
    "marketing": "Marketing Analyst",
    "cto": "CTO",
}

# Fallback redaction policy if config file is missing
DEFAULT_POLICY: Dict[str, Dict[str, str]] = {
    "email": {"enabled": True, "pattern": r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b", "token": "[REDACTED:EMAIL]"},
    "ipv6": {
        "enabled": True,
        "pattern": r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b",
        "token": "[REDACTED:IPV6]",
    },
    "street_address": {
        "enabled": True,
        "pattern": r"\b\d+\s+[A-Za-z0-9.\s]+\b",
        "token": "[REDACTED:ADDRESS]",
    },
}


def load_redaction_policy() -> Dict[str, Dict[str, str]]:
    """Load the redaction policy; fall back to an in-code default.

    Redaction can be globally disabled by setting the environment variable
    ``DRRD_ENABLE_PROMPT_REDACTION`` to a falsy value (default). When disabled,
    all rules are returned with ``enabled=False`` so that callers can skip
    redaction without altering call sites.
    """

    path = Path(__file__).resolve().parents[1] / "config" / "redaction.yaml"
    try:
        policy = _load_policy(path)
    except FileNotFoundError:
        policy = DEFAULT_POLICY

    if os.getenv("DRRD_ENABLE_PROMPT_REDACTION", "").lower() not in {"1", "true", "yes"}:
        for cfg in policy.values():
            cfg["enabled"] = False
    return policy


def redact_text(policy: Dict[str, Dict[str, str]], text: str) -> str:
    """Apply redaction and ensure idempotency."""
    once = _redact(text, policy=policy)
    twice = _redact(once, policy=policy)
    return twice


def segment_concept_brief(brief: ConceptBrief) -> List[TaskSpec]:
    policy = load_redaction_policy()
    tasks: List[TaskSpec] = []
    if not brief.success_metrics:
        return tasks
    for metric in brief.success_metrics:
        for responsibility, role in RESPONSIBILITY_TO_ROLE.items():
            task_text = f"{responsibility.title()} perspective on '{metric}' for {brief.problem}"
            task_text = redact_text(policy, task_text)
            tasks.append(TaskSpec(role=role, task=task_text))
    return tasks
