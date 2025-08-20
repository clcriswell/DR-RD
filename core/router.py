"""Simple task-to-agent routing utilities."""

from __future__ import annotations

from typing import Dict, Tuple, Type

from core.agents.registry import AGENT_REGISTRY

# ---------------------------------------------------------------------------
# Lightweight keyword heuristics
# ---------------------------------------------------------------------------
# Map lowercase keywords to the canonical role they imply.  This dictionary is
# intentionally small; it only covers a few common business domains and can be
# extended as needed.
KEYWORDS: Dict[str, str] = {
    "market": "Marketing Analyst",
    "customer": "Marketing Analyst",
    "patent": "IP Analyst",
    "regulatory": "Regulatory",
    "compliance": "Regulatory",
    "fda": "Regulatory",
    "iso": "Regulatory",
    "budget": "Finance",
    "architecture": "CTO",
}


def choose_agent_for_task(
    planned_role: str | None, title: str, description: str
) -> Tuple[str, Type]:
    """Return the canonical role and agent class for a task.

    Parameters
    ----------
    planned_role:
        Role suggested by upstream planning.  If this matches a key in
        ``AGENT_REGISTRY`` it is returned immediately.
    title / description:
        Text describing the task.  These are scanned for keywords if no exact
        role match is found.

    Returns
    -------
    Tuple[str, Type]
        The resolved role name and its agent class.
    """

    # 1) Exact match on planned_role via the central registry
    if planned_role and planned_role in AGENT_REGISTRY:
        return planned_role, AGENT_REGISTRY[planned_role]

    # 2) Keyword heuristics over title + description
    text = f"{title} {description}".lower()
    for kw, role in KEYWORDS.items():
        if kw in text and role in AGENT_REGISTRY:
            return role, AGENT_REGISTRY[role]

    # 3) Default to Research Scientist
    return "Research Scientist", AGENT_REGISTRY["Research Scientist"]


__all__ = ["choose_agent_for_task", "KEYWORDS"]

