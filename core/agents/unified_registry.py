from __future__ import annotations

import logging
import os
from typing import Dict, Tuple, Optional, TYPE_CHECKING

# Import BaseAgent only for type checking to avoid circular imports.
if TYPE_CHECKING:  # pragma: no cover - for static typing only
    from agents.base_agent import BaseAgent
# Import the canonical small set that we KNOW take (model) in ctor:
from core.agents.cto import CTOAgent
from core.agents.research_scientist import ResearchScientistAgent
from core.agents.regulatory import RegulatoryAgent
from core.agents.finance import FinanceAgent
from core.agents.marketing import MarketingAgent
from core.agents.ip_analyst import IPAnalystAgent
from agents.planner_agent import PlannerAgent
from agents.synthesizer import SynthesizerAgent

logger = logging.getLogger("unified_registry")

# Model selection (centralized)
def resolve_model(role: str, purpose: str = "exec") -> str:
    """
    purpose: 'exec' | 'plan' | 'synth'
    Uses environment overrides to decide model. Defaults to ``gpt-5`` for all
    profiles.
    """
    profile = os.getenv("DRRD_PROFILE", "deep").lower()
    if purpose == "plan":
        return os.getenv("DRRD_MODEL_PLAN", "gpt-5")
    if purpose == "synth":
        return os.getenv("DRRD_MODEL_SYNTH", "gpt-5")
    if profile == "test":
        return os.getenv("DRRD_MODEL_EXEC_TEST", "gpt-5")
    if profile == "pro":
        return os.getenv("DRRD_MODEL_EXEC_PRO", "gpt-5")
    if profile == "deep":
        return os.getenv("DRRD_MODEL_EXEC_DEEP", "gpt-5")
    return os.getenv("DRRD_MODEL_EXEC_EFFICIENT", "gpt-5")

def build_agents_unified(
    overrides: Dict[str, str] | None = None,
    default_model: Optional[str] = None,
) -> Dict[str, BaseAgent]:
    """Instantiate the core set of agents.

    Parameters
    ----------
    overrides: mapping of role to model id to force specific models.
    default_model: fallback model if a role is not in overrides.
    """

    overrides = overrides or {}

    def _model(role: str, purpose: str = "exec") -> str:
        return overrides.get(role) or default_model or resolve_model(role, purpose)

    agents: Dict[str, BaseAgent] = {}
    # Core business roles
    agents["CTO"] = CTOAgent(_model("CTO"))
    agents["Research Scientist"] = ResearchScientistAgent(_model("Research Scientist"))
    agents["Regulatory"] = RegulatoryAgent(_model("Regulatory"))
    agents["Finance"] = FinanceAgent(_model("Finance"))
    agents["Marketing Analyst"] = MarketingAgent(_model("Marketing Analyst"))
    agents["IP Analyst"] = IPAnalystAgent(_model("IP Analyst"))
    # Planner / Synthesizer
    agents["Planner"] = PlannerAgent(_model("Planner", "plan"))
    agents["Synthesizer"] = SynthesizerAgent(_model("Synthesizer", "synth"))

    # Try to import legacy specialist agents, but don’t fail the build if their
    # constructors differ. They remain available for fallback routing.
    try:
        from agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
        agents["Mechanical Systems Lead"] = MechanicalSystemsLeadAgent(resolve_model("Mechanical Systems Lead"))
    except Exception as e:
        logger.warning("Could not instantiate legacy agent MechanicalSystemsLeadAgent: %s", e)

    # (Repeat pattern for a handful of legacy specialists you still want.)
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
    default = agents.get("Research Scientist") or next(iter(agents.values()))
    for k in ["Marketing Analyst","IP Analyst","Finance"]:
        if k not in agents:
            agents[k] = default
    return agents

def choose_agent_for_task(planned_role: str, title: str, desc: Optional[str], agents: Dict[str, BaseAgent]) -> Tuple[str, BaseAgent]:
    # Exact match first
    agent = agents.get(planned_role)
    if agent:
        return planned_role, agent

    low = f"{title} {desc or ''}".lower()
    if any(k in low for k in ["market","position","segment","competitor","pricing"]):
        a = agents.get("Marketing Analyst")
        if a: return "Marketing Analyst", a
    if any(k in low for k in ["budget","cost","price","roi","capex","opex"]):
        a = agents.get("Finance")
        if a: return "Finance", a

    # Default
    routed_role = "Research Scientist" if "Research Scientist" in agents else next(iter(agents.keys()))
    return routed_role, agents[routed_role]
