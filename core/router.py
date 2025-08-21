"""Simple task-to-agent routing utilities."""

from __future__ import annotations

import logging
from typing import Dict, Tuple, Type

from core.agents.registry import AGENT_REGISTRY
from core.llm import select_model

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


ROLE_SYNONYMS: Dict[str, str] = {
    "Project Manager": "Planner",
    "Program Manager": "Planner",
    "Product Manager": "Planner",
    "Risk Manager": "Regulatory",
}


def _alias(role: str | None) -> str | None:
    if not role:
        return role
    return ALIASES.get(role.strip().lower(), role)


def choose_agent_for_task(
    planned_role: str | None,
    title: str,
    description: str,
    ui_model: str | None = None,
) -> Tuple[str, Type, str]:
    """Return the canonical role, agent class, and model for a task.

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
    if role:
        role = ROLE_SYNONYMS.get(role, role)
    if role and role in AGENT_REGISTRY:
        model = select_model("agent", ui_model, agent_name=role)
        return role, AGENT_REGISTRY[role], model

    # 2) Keyword heuristics over title + description
    text = f"{title} {description}".lower()
    for kw, role in KEYWORDS.items():
        if kw in text and role in AGENT_REGISTRY:
            model = select_model("agent", ui_model, agent_name=role)
            return role, AGENT_REGISTRY[role], model

    # 3) Fallback to Synthesizer with info log
    if planned_role:
        logger.info("Fallback routing %r → Synthesizer", planned_role)
    model = select_model("agent", ui_model, agent_name="Synthesizer")
    return "Synthesizer", AGENT_REGISTRY["Synthesizer"], model


def route_task(
    task: Dict[str, str], ui_model: str | None = None
) -> Tuple[str, Type, str, Dict[str, str]]:
    """Resolve role/agent for a task dict without dropping fields."""
    role, cls, model = choose_agent_for_task(
        task.get("role"), task.get("title", ""), task.get("description", ""), ui_model
    )
    out = dict(task)
    out["role"] = role
    out.setdefault("stop_rules", task.get("stop_rules", []))
    return role, cls, model, out


__all__ = ["choose_agent_for_task", "KEYWORDS", "ALIASES", "ROLE_SYNONYMS", "route_task"]

