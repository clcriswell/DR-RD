from typing import Dict, List, Tuple
import re
import logging

from agents.generic_domain_agent import GenericDomainAgent

log = logging.getLogger(__name__)

# Aliases to handle common naming mismatches from the Planner
ROLE_ALIASES: Dict[str, str] = {
    # broad roles you plan for in README
    "Research Scientist": "Research",
    "Regulatory": "Regulatory",
    "Finance": "Finance",
    "CTO": "CTO",
    "Marketing Analyst": "Marketing Analyst",
    "IP Analyst": "IP Analyst",
}

# Optional tags -> specialist roles (extend to your specialists if desired)
TAG_TO_ROLE: Dict[str, str] = {
    "mechanical": "Mechanical Systems Lead",
    "optics": "Optical Systems Engineer",
    "photonics": "Photonics Electronics Engineer",
    "materials": "Materials Scientist",
    "electronics": "Electronics Engineer",
    "software": "Software/ML Engineer",
    "thermal": "Thermal Engineer",
    "qa": "QA/Testing Lead",
    "regulatory": "Regulatory",
    "finance": "Finance",
    "marketing": "Marketing Analyst",
    "ip": "IP Analyst",
}

# Lightweight keyword buckets for fallback routing
KEYWORDS: Dict[str, List[str]] = {
    "Marketing Analyst": ["market", "segment", "competition", "pricing", "revenue", "adoption", "tam", "sam", "som", "gtm"],
    "IP Analyst": ["patent", "prior art", "claims", "novelty", "patentability", "fto", "freedom to operate"],
    "Finance": ["budget", "cost", "capex", "opex", "bom", "unit economics", "roi", "breakeven", "payback"],
    "Regulatory": ["regulatory", "compliance", "fda", "hipaa", "gdpr", "ce", "iso", "510(k)", "510k"],
    "CTO": ["architecture", "system design", "tech strategy", "roadmap"],
    # specialist hints (optional)
    "Mechanical Systems Lead": ["mechanical", "fixture", "frame", "actuator", "gear", "stress", "strain"],
    "Optical Systems Engineer": ["optical", "lens", "objective", "na", "interferometer", "microscope", "diffraction", "entanglement"],
    "Materials Scientist": ["material", "coating", "substrate", "alloy", "polymer", "film"],
    "Electronics Engineer": ["circuit", "pcb", "adc", "fpga", "driver", "amplifier", "dac"],
    "Software/ML Engineer": ["pipeline", "inference", "training", "dataset", "api", "opencv"],
    "Thermal Engineer": ["thermal", "heat sink", "convection", "temperature", "cooling"],
    "QA/Testing Lead": ["test plan", "validation", "verification", "acceptance criteria"],
    "Research": [],  # safe default
}


def _norm(s: str) -> str:
    return (s or "").strip()


def normalize_role(planned_role: str) -> str:
    pr = _norm(planned_role)
    return ROLE_ALIASES.get(pr, pr)


def choose_agent_for_task(
    planned_role: str,
    title: str,
    description: str,
    tags: List[str],
    agents: Dict[str, object],
) -> Tuple[object, str]:
    """
    Returns (agent_instance, routed_role_name) without dropping any task.
    Order: exact/alias -> tags -> keywords -> default
    """
    # 1) exact or alias
    cand = normalize_role(planned_role)
    if cand in agents:
        return agents[cand], cand
    # 2) tags to specialists
    for t in (tags or []):
        r = TAG_TO_ROLE.get(_norm(t).lower())
        if r and r in agents:
            return agents[r], r
    # 3) keyword buckets (title+description)
    text = f"{title or ''} {description or ''}".lower()
    for role, words in KEYWORDS.items():
        if role in agents and any(re.search(rf"\b{re.escape(w)}\b", text) for w in words):
            return agents[role], role
    # 4) generic specialist fallback
    agent = resolve_agent_for_role(planned_role, agents)
    return agent, getattr(agent, "name", planned_role or "Research")


def resolve_agent_for_role(role: str, agents: dict):
    role_norm = normalize_role(role)
    if role_norm in agents:
        return agents[role_norm]
    if not role_norm:
        base = agents.get("Research") or next(iter(agents.values()))
        return base
    log.info("No concrete agent for role '%s'; using GenericDomainAgent", role_norm)
    base = agents.get("Research Scientist") or agents.get("CTO") or next(iter(agents.values()))
    model = getattr(base, "model", None) or "gpt-4o-mini"
    g = GenericDomainAgent(role=role_norm, model=model)
    agents[role_norm] = g
    return g
