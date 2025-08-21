from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Dict, Optional, Tuple

import core

# Import BaseAgent only for type checking to avoid circular imports.
if TYPE_CHECKING:  # pragma: no cover - for static typing only
    from core.agents.base_agent import BaseAgent

from core.agents.registry import get_agent_class

logger = logging.getLogger("unified_registry")


# Model selection (centralized)
def resolve_model(role: str, purpose: str = "exec") -> str:
    """
    purpose: 'exec' | 'plan' | 'synth'
    Uses environment overrides to decide model. Defaults to ``gpt-4.1-mini`` for most
    profiles and ``gpt-4-turbo`` for ``test`` unless overridden.
    """
    profile = os.getenv("DRRD_PROFILE", "deep").lower()
    default_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if purpose == "plan":
        return os.getenv("DRRD_MODEL_PLAN") or default_model
    if purpose == "synth":
        return os.getenv("DRRD_MODEL_SYNTH") or default_model
    if profile == "test":
        return os.getenv("DRRD_MODEL_EXEC_TEST") or os.getenv("OPENAI_MODEL") or "gpt-4-turbo"
    if profile == "pro":
        return os.getenv("DRRD_MODEL_EXEC_PRO") or default_model
    if profile == "deep":
        return os.getenv("DRRD_MODEL_EXEC_DEEP") or default_model
    return os.getenv("DRRD_MODEL_EXEC_EFFICIENT") or default_model


def build_agents_unified(
    overrides: Dict[str, str] | None = None,
    default_model: Optional[str] = None,
) -> Dict[str, BaseAgent]:
    """Instantiate the core set of core.agents.

    Parameters
    ----------
    overrides: mapping of role to model id to force specific models.
    default_model: fallback model if a role is not in overrides.
    """

    overrides = overrides or {}

    def _model(role: str, purpose: str = "exec") -> str:
        return overrides.get(role) or default_model or resolve_model(role, purpose)

    agents: Dict[str, BaseAgent] = {}

    for role in [
        "CTO",
        "Research Scientist",
        "Regulatory",
        "Finance",
        "Marketing Analyst",
        "IP Analyst",
        "Planner",
        "Synthesizer",
    ]:
        cls = get_agent_class(role)
        if not cls:
            continue
        purpose = "plan" if role == "Planner" else "synth" if role == "Synthesizer" else "exec"
        agents[role] = cls(_model(role, purpose))

    # Try to instantiate optional legacy specialists via the registry
    for legacy_role in ["Mechanical Systems Lead"]:
        cls = get_agent_class(legacy_role)
        if not cls:
            try:
                from core.agents.mechanical_systems_lead_agent import (
                    MechanicalSystemsLeadAgent as cls,  # type: ignore
                )
            except Exception as e:  # pragma: no cover - best effort
                logger.warning("Could not instantiate legacy agent %s: %s", legacy_role, e)
                cls = None
        if cls:
            try:
                agents[legacy_role] = cls(resolve_model(legacy_role))  # type: ignore[arg-type]
            except Exception as e:  # pragma: no cover - best effort
                logger.warning("Failed to create legacy agent %s with error: %s", legacy_role, e)

    return agents


def ensure_canonical_agent_keys(agents: Dict[str, BaseAgent]) -> Dict[str, BaseAgent]:
    # Provide common shims; never fail if some are missing.
    if "Regulatory" not in agents and "Regulatory & Compliance Lead" in agents:
        agents["Regulatory"] = agents["Regulatory & Compliance Lead"]
    if "Research Scientist" not in agents and "Research" in agents:
        agents["Research Scientist"] = agents["Research"]
    if "CTO" not in agents and "AI R&D Coordinator" in agents:
        agents["CTO"] = agents["AI R&D Coordinator"]
    # Business-role graceful fallbacks
    default = core.agents.get("Research Scientist") or next(iter(core.agents.values()))
    for k in ["Marketing Analyst", "IP Analyst", "Finance"]:
        if k not in agents:
            agents[k] = default
    return agents


def choose_agent_for_task(
    planned_role: str, title: str, desc: Optional[str], agents: Dict[str, BaseAgent]
) -> Tuple[str, BaseAgent]:
    # Exact match first
    agent = core.agents.get(planned_role)
    if agent:
        return planned_role, agent

    low = f"{title} {desc or ''}".lower()
    if any(k in low for k in ["market", "position", "segment", "competitor", "pricing"]):
        a = core.agents.get("Marketing Analyst")
        if a:
            return "Marketing Analyst", a
    if any(k in low for k in ["budget", "cost", "price", "roi", "capex", "opex"]):
        a = core.agents.get("Finance")
        if a:
            return "Finance", a

    # Default
    routed_role = (
        "Research Scientist" if "Research Scientist" in agents else next(iter(core.agents.keys()))
    )
    return routed_role, agents[routed_role]
