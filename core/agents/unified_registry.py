import logging
import os
from typing import Dict, Tuple, Optional
from core.roles import canonical_roles
from agents.base_agent import BaseAgent  # ensure single BaseAgent with .run
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
    Uses profile/env to decide model. Defaults ensure Deep/Pro use non-mini.
    """
    profile = os.getenv("DRRD_PROFILE", "Pro").lower()
    # env overrides
    if purpose == "plan":
        return os.getenv("DRRD_MODEL_PLAN", "gpt-4o")
    if purpose == "synth":
        return os.getenv("DRRD_MODEL_SYNTH", "gpt-4o")
    # exec:
    if profile in ("pro","deep"):
        return os.getenv("DRRD_MODEL_EXEC_PRO", "gpt-4o")
    if profile in ("balanced",):
        return os.getenv("DRRD_MODEL_EXEC_BALANCED", "gpt-4o-mini")
    # efficient / default
    return os.getenv("DRRD_MODEL_EXEC_EFFICIENT", "gpt-4o-mini")

def build_agents_unified() -> Dict[str, BaseAgent]:
    agents: Dict[str, BaseAgent] = {}
    # Core business roles
    agents["CTO"] = CTOAgent(resolve_model("CTO"))
    agents["Research Scientist"] = ResearchScientistAgent(resolve_model("Research Scientist"))
    agents["Regulatory"] = RegulatoryAgent(resolve_model("Regulatory"))
    agents["Finance"] = FinanceAgent(resolve_model("Finance"))
    agents["Marketing Analyst"] = MarketingAgent(resolve_model("Marketing Analyst"))
    agents["IP Analyst"] = IPAnalystAgent(resolve_model("IP Analyst"))
    # Planner / Synthesizer
    agents["Planner"] = PlannerAgent(resolve_model("Planner","plan"))
    agents["Synthesizer"] = SynthesizerAgent(resolve_model("Synthesizer","synth"))

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
