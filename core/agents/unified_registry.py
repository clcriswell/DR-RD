from __future__ import annotations
from typing import Dict, Tuple, Iterable
import importlib, pkgutil, inspect, logging

log = logging.getLogger("unified_registry")

# Light alias map so synonyms converge
ALIASES = {
    "research": "Research Scientist",
    "research scientist": "Research Scientist",
    "regulatory & compliance lead": "Regulatory",
    "chief technology officer": "CTO",
    "marketing": "Marketing Analyst",
    "ip": "IP Analyst",
}

def _canon(name: str) -> str:
    if not name: return ""
    key = name.strip()
    low = key.lower()
    return ALIASES.get(low, key)

def _iter_agent_classes(pkg_mod) -> Iterable[Tuple[str, type]]:
    """Yield (role_name, class) for classes that look like agents."""
    base = pkg_mod.__name__
    for _, modname, _ in pkgutil.walk_packages(pkg_mod.__path__, base + "."):
        try:
            m = importlib.import_module(modname)
        except Exception:
            continue
        for _, obj in inspect.getmembers(m, inspect.isclass):
            if not obj.__module__.startswith(m.__name__):
                continue
            # Heuristic: must have a .run(...) method
            if not hasattr(obj, "run"):
                continue
            role = getattr(obj, "ROLE", None) or getattr(obj, "NAME", None) or getattr(obj, "__name__", None)
            if isinstance(role, str) and role:
                yield _canon(role), obj

def _discover_legacy() -> Dict[str, type]:
    found: Dict[str, type] = {}
    for pkg_name in ("agents", "dr_rd.agents"):
        try:
            pkg = importlib.import_module(pkg_name)
        except Exception:
            continue
        for role, cls in _iter_agent_classes(pkg):
            # keep first occurrence; core will override later
            found.setdefault(role, cls)
    return found

def build_agents_unified(agent_model_map: Dict[str, str], default_model: str | None = None) -> Dict[str, object]:
    """
    Prefer core agents; backfill with any legacy agents discovered in /agents and /dr_rd/agents.
    Returns {role: agent_instance}.
    """
    # 1) Start with core registry
    from core.agents.registry import build_agents as _build_core
    agents = _build_core()

    # 2) Backfill: if canonical keys are missing but legacy classes exist, instantiate them
    legacy = _discover_legacy()
    for role, cls in legacy.items():
        if role in agents:
            continue
        try:
            model = agent_model_map.get(role, default_model)
            agents[role] = cls(model) if model is not None else cls()
        except Exception as e:
            log.warning("Could not instantiate legacy agent %s: %s", role, e)

    # 3) Provide common alias keys to avoid planner/registry mismatch
    if "Regulatory" not in agents and "Regulatory & Compliance Lead" in agents:
        agents["Regulatory"] = agents["Regulatory & Compliance Lead"]
    if "Research Scientist" not in agents and "Research" in agents:
        agents["Research Scientist"] = agents["Research"]
    if "CTO" not in agents and "AI R&D Coordinator" in agents:
        agents["CTO"] = agents["AI R&D Coordinator"]

    return agents
