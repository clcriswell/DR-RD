from typing import Dict, List, Tuple, Optional
import re
import logging
import importlib, inspect, pkgutil
import core

from core.agents.generic_domain_agent import GenericDomainAgent

log = logging.getLogger(__name__)

# Expanded alias map (lowercase keys)
ALIASES = {
    # generic
    "research": "Research Scientist",
    "researcher": "Research Scientist",
    "regulatory compliance officer": "Regulatory",
    "regulatory lead": "Regulatory",
    "ip": "IP Analyst",
    "ip analyst": "IP Analyst",
    "marketing": "Marketing Analyst",
    "marketing analyst": "Marketing Analyst",
    # optics & photonics
    "optical systems designer": "Optical Systems Engineer",
    "optical systems engineer": "Optical Systems Engineer",
    "entangled photon source designer": "Quantum Optics Physicist",
    "quantum optics physicist": "Quantum Optics Physicist",
    "nonlinear optical crystal engineer": "Nonlinear Optics / Crystal Engineer",
    "photonics signal processing engineer": "Photonics Electronics Engineer",
    # software / ai / data
    "software & image-processing specialist": "Software & Image-Processing Specialist",
    "image processing specialist": "Software & Image-Processing Specialist",
    "ai algorithm developer": "AI R&D Coordinator",
    "machine learning specialist": "AI R&D Coordinator",
    "ai r&d coordinator": "AI R&D Coordinator",
    "data visualization expert": "Software & Image-Processing Specialist",
    # systems / electronics / validation
    "embedded systems engineer": "Electronics & Embedded Controls Engineer",
    "electronics & embedded controls engineer": "Electronics & Embedded Controls Engineer",
    "systems integration & validation manager": "Systems Integration & Validation Manager",
    "quantum systems integration specialist": "Systems Integration & Validation Manager",
    "validation and testing engineer": "Systems Integration & Validation Manager",
}


def _alias_role(role: str) -> str:
    if not role:
        return role
    r = " ".join(role.split()).strip()
    low = r.lower()
    return ALIASES.get(low, r)


# Attempt to import a specialist agent class matching the role.
# Strategy: convert role to CamelCase + 'Agent', then scan core.agents.* modules.
def _try_load_specialist_class(role: str) -> Optional[type]:
    if not role:
        return None
    tokens = [t for t in "".join(ch if ch.isalnum() else " " for ch in role).split() if t]
    if not tokens:
        return None
    class_guess = "".join(w.capitalize() for w in tokens) + "Agent"
    try:
        import core.agents as agents
        for m in pkgutil.iter_modules(core.agents.__path__):
            mod = importlib.import_module(f"core.agents.{m.name}")
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                # exact match first
                if name.lower() == class_guess.lower():
                    return obj
                # fallback: partial token match
                if name.lower().endswith("agent"):
                    nm = name.lower().replace("agent", "").strip()
                    if all(tok.lower() in nm for tok in [t.lower() for t in tokens if len(t) > 2]):
                        return obj
    except Exception:
        return None
    return None

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
    "Research Scientist": [],  # safe default
}


def _norm(s: str) -> str:
    return (s or "").strip()


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
    cand = _alias_role(planned_role)
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
    return agent, getattr(agent, "name", planned_role or "Research Scientist")


def resolve_agent_for_role(role: str, agents: dict):
    # Normalize by alias first
    role_norm = _alias_role(role)
    if role_norm != role:
        role = role_norm

    if role in agents:
        return agents[role]
    if not role:
        base = core.agents.get("Research Scientist") or core.agents.get("CTO") or next(iter(core.agents.values()))
        return base

    # Try to preload a specialist class if available
    try:
        Specialist = _try_load_specialist_class(role)
        if Specialist is not None:
            base = core.agents.get("Research Scientist") or core.agents.get("CTO")
            kw = {}
            if base and hasattr(base, "model"):
                kw["model"] = getattr(base, "model")
            spec = Specialist(**kw)
            agents[role] = spec
            log.info("Loaded specialist agent for role '%s' via class %s", role, Specialist.__name__)
            return spec
    except Exception:
        log.exception("Specialist preload failed for role '%s'", role)

    log.info("No concrete agent for role '%s'; using GenericDomainAgent", role)
    base = core.agents.get("Research Scientist") or core.agents.get("CTO") or next(iter(core.agents.values()))
    model = getattr(base, "model", None) or "gpt-5"
    g = GenericDomainAgent(role=role, model=model)
    agents[role] = g
    return g
