from __future__ import annotations

import logging
import os
from typing import Dict, Optional, Tuple, Type

from core.agents.base_agent import LLMRoleAgent as BaseAgent
from core.agents.cto_agent import CTOAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.regulatory_agent import RegulatoryAgent
from core.agents.finance_agent import FinanceAgent
from core.agents.marketing_agent import MarketingAgent
from core.agents.ip_analyst_agent import IPAnalystAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.synthesizer_agent import SynthesizerAgent
from core.agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from core.agents.hrm_agent import HRMAgent
from core.agents.materials_engineer_agent import MaterialsEngineerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.chief_scientist_agent import ChiefScientistAgent
from core.agents.regulatory_specialist_agent import RegulatorySpecialistAgent
from core.agents.invoke import resolve_invoker
from core.llm import select_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical registry
# ---------------------------------------------------------------------------
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "CTO": CTOAgent,
    "Research Scientist": ResearchScientistAgent,
    "Regulatory": RegulatoryAgent,
    "Finance": FinanceAgent,
    "Marketing Analyst": MarketingAgent,
    "IP Analyst": IPAnalystAgent,
    "Planner": PlannerAgent,
    "Synthesizer": SynthesizerAgent,
    "Mechanical Systems Lead": MechanicalSystemsLeadAgent,
    "HRM": HRMAgent,
    "Materials Engineer": MaterialsEngineerAgent,
    "Reflection": ReflectionAgent,
    "Chief Scientist": ChiefScientistAgent,
    "Regulatory Specialist": RegulatorySpecialistAgent,
}

# Backwards compatibility alias
AGENTS = AGENT_REGISTRY

CACHE: Dict[str, BaseAgent] = {}


def get_agent_class(role: str) -> Optional[Type[BaseAgent]]:
    return AGENT_REGISTRY.get(role)


def get_agent(name: str) -> BaseAgent:
    if name in CACHE:
        return CACHE[name]
    cls = get_agent_class(name) or AGENT_REGISTRY["Research Scientist"]
    inst = cls(select_model("agent", agent_name=name))
    CACHE[name] = inst
    return inst


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def validate_registry(strict: bool | None = None) -> dict:
    ok: list[str] = []
    errors: list[tuple[str, str]] = []
    for name, cls in AGENT_REGISTRY.items():
        try:
            inst = cls(select_model("agent", agent_name=name))
            CACHE.setdefault(name, inst)
            resolve_invoker(inst)
            ok.append(name)
        except Exception as e:  # pragma: no cover - best effort
            errors.append((name, str(e)))
    logger.info("agent registry validation: ok=%d errors=%d", len(ok), len(errors))
    if errors:
        logger.info("non-callable agents: %s", [n for n, _ in errors])
    env_strict = os.getenv("DRRD_STRICT_AGENT_REGISTRY", "").lower() == "true"
    if (strict or env_strict) and errors:
        raise RuntimeError("Agent registry validation failed")
    return {"ok": ok, "errors": errors}


def build_agents_unified(mapping: Dict[str, str], default_model: str) -> Dict[str, BaseAgent]:
    agents: Dict[str, BaseAgent] = {}
    for role, cls in AGENT_REGISTRY.items():
        model = mapping.get(role, default_model)
        try:
            agents[role] = cls(model)
        except Exception as e:  # pragma: no cover - best effort
            logger.warning("Failed to instantiate %s: %s", role, e)
    return agents


def ensure_canonical_agent_keys(agents: Dict[str, BaseAgent]) -> Dict[str, BaseAgent]:
    if "Regulatory" not in agents and "Regulatory Specialist" in agents:
        agents["Regulatory"] = agents["Regulatory Specialist"]
    if "Research Scientist" not in agents and "Research" in agents:
        agents["Research Scientist"] = agents["Research"]
    if "CTO" not in agents and "AI R&D Coordinator" in agents:
        agents["CTO"] = agents["AI R&D Coordinator"]
    default = agents.get("Research Scientist") or next(iter(agents.values()))
    for k in ["Marketing Analyst", "IP Analyst", "Finance"]:
        agents.setdefault(k, default)
    return agents


def choose_agent_for_task(
    planned_role: str,
    title: str,
    desc: Optional[str],
    agents: Dict[str, BaseAgent],
) -> Tuple[str, BaseAgent]:
    from core.router import choose_agent_for_task as router_choose

    resolved, _cls, _model = router_choose(planned_role, title, desc or "", None)
    agent = agents.get(resolved) or agents.get("Research Scientist")
    return resolved, agent


# ---------------------------------------------------------------------------
# Model selection (legacy resolver used by tests)
# ---------------------------------------------------------------------------

def resolve_model(role: str, purpose: str = "exec") -> str:
    profile = os.getenv("DRRD_PROFILE", "standard").lower()
    if profile in {"test", "deep"}:
        logging.warning("DRRD_PROFILE '%s' is deprecated; using 'standard'.", profile)
        profile = "standard"
    default_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if purpose == "plan":
        return os.getenv("DRRD_MODEL_PLAN") or ("gpt-5" if profile == "pro" else default_model)
    if purpose == "synth":
        return os.getenv("DRRD_MODEL_SYNTH") or ("gpt-5" if profile == "pro" else default_model)
    if profile == "pro":
        return os.getenv("DRRD_MODEL_EXEC_PRO") or "gpt-5"
    return os.getenv("DRRD_MODEL_EXEC_EFFICIENT") or default_model

