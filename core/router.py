"""Simple task-to-agent routing utilities."""

from __future__ import annotations

import logging
from typing import Dict, Tuple, Type

from core.agents.registry import AGENT_REGISTRY

logger = logging.getLogger(__name__)

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

# Common role aliases to canonical registry roles
ALIASES: Dict[str, str] = {
    "manufacturing technician": "Research Scientist",
}


def _alias(role: str | None) -> str | None:
    if not role:
        return role
    return ALIASES.get(role.strip().lower(), role)


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
    role = _alias(planned_role)
    if role and role in AGENT_REGISTRY:
        return role, AGENT_REGISTRY[role]

    # 2) Keyword heuristics over title + description
    text = f"{title} {description}".lower()
    for kw, role in KEYWORDS.items():
        if kw in text and role in AGENT_REGISTRY:
            return role, AGENT_REGISTRY[role]

    # 3) Default to Research Scientist with warning
    if planned_role:
        logger.warning("Unresolved role: %s", planned_role)
    return "Research Scientist", AGENT_REGISTRY["Research Scientist"]


def route_task(task: Dict[str, str]) -> Tuple[str, Type, Dict[str, str]]:
    """Resolve role/agent for a task dict without dropping fields."""
    role, cls = choose_agent_for_task(
        task.get("role"), task.get("title", ""), task.get("description", "")
    )
    out = dict(task)
    out["role"] = role
    out.setdefault("stop_rules", task.get("stop_rules", []))
    return role, cls, out


__all__ = ["choose_agent_for_task", "KEYWORDS", "ALIASES", "route_task"]

