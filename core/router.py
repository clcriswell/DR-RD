"""Simple task-to-agent routing utilities."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Type

import yaml

from config import feature_flags
from core.agents.invoke import invoke_agent
from core.agents.unified_registry import AGENT_REGISTRY, get_agent
from core.llm import select_model
from core.roles import canonicalize

logger = logging.getLogger(__name__)
BUDGETS: Dict[str, Any] | None = None
RAG_CFG = yaml.safe_load(Path("config/rag.yaml").read_text()) if Path("config/rag.yaml").exists() else {}


def _load_budgets() -> Dict[str, Any]:
    global BUDGETS
    if BUDGETS is None:
        cfg_path = Path(__file__).resolve().parents[1] / "config" / "budgets.yaml"
        with open(cfg_path, "r", encoding="utf-8") as fh:
            BUDGETS = yaml.safe_load(fh) or {}
    profile = feature_flags.BUDGET_PROFILE
    return BUDGETS.get(profile, {})


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
    "prior art": "IP Analyst",
    "cpc": "IP Analyst",
    "ipc": "IP Analyst",
    "publication": "IP Analyst",
    "claims": "IP Analyst",
    "assignee": "IP Analyst",
    "cfr": "Regulatory",
    "docket": "Regulatory",
    "final rule": "Regulatory",
    "510(k)": "Regulatory",
    "pma": "Regulatory",
    "regulations.gov": "Regulatory",
    "iso": "Regulatory",
    "budget": "Finance",
    "architecture": "CTO",
    # Expanded coverage
    "quantum": "Research Scientist",
    "physics": "Research Scientist",
    "physicist": "Research Scientist",
    "materials": "Materials Engineer",
    "manufacturing": "Materials Engineer",
    "prototype": "Materials Engineer",
    "hr": "HRM",
    "human resources": "HRM",
    "hiring": "HRM",
    "org design": "HRM",
    "qa": "QA",
    "quality assurance": "QA",
    "consistency review": "Reflection",
    "postmortem": "Reflection",
    "material": "Materials",
    "alloy": "Materials",
    "polymer": "Materials",
    "tensile": "Materials",
    "modulus": "Materials",
    "test plan": "QA",
    "requirement": "QA",
    "coverage": "QA",
    "defect": "QA",
    "quality": "QA",
    "unit economics": "Finance Specialist",
    "npv": "Finance Specialist",
    "irr": "Finance Specialist",
    "pricing": "Finance Specialist",
    "margin": "Finance Specialist",
    "simulate": "Simulation",
    "model": "Simulation",
    "digital twin": "Simulation",
    "param sweep": "Simulation",
    "monte carlo": "Simulation",
}

# Common role aliases to canonical registry roles
ALIASES: Dict[str, str] = {
    "manufacturing technician": "Research Scientist",
    "quantum physicist": "Research Scientist",
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
    role = canonicalize(_alias(planned_role))
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

    # 3) Fallback to Dynamic Specialist
    model = select_model("agent", ui_model, agent_name="Dynamic Specialist")
    return "Dynamic Specialist", AGENT_REGISTRY["Dynamic Specialist"], model


def route_task(
    task: Dict[str, str], ui_model: str | None = None
) -> Tuple[str, Type, str, Dict[str, str]]:
    """Resolve role/agent for a task dict without dropping fields."""
    planned = task.get("role")
    if task.get("hints", {}).get("simulation_domain"):
        planned = "Simulation"
    role, cls, model = choose_agent_for_task(
        planned, task.get("title", ""), task.get("description", ""), ui_model
    )
    out = dict(task)
    out["role"] = role
    out.setdefault("stop_rules", task.get("stop_rules", []))

    route_decision: Dict[str, Any] = {"selected_role": role}
    if feature_flags.COST_GOVERNANCE_ENABLED:
        budgets = _load_budgets()
        exec_cfg = budgets.get("exec", {})
        route_cfg = budgets.get("route", {})
        retrieval_level = exec_cfg.get("retrieval_policy_default", "AGGRESSIVE")
        topk_map = RAG_CFG.get("topk_defaults", {})
        route_decision.update(
            {
                "budget_profile": feature_flags.BUDGET_PROFILE,
                "retrieval_level": retrieval_level,
                "top_k_applied": topk_map.get(retrieval_level, 0),
                "per_doc_cap_tokens": RAG_CFG.get("per_doc_cap_tokens", 400),
                "dense_enabled": bool(os.getenv("OPENAI_API_KEY")),
                "caps": {
                    "max_tool_calls": exec_cfg.get("max_tool_calls"),
                    "max_parallel_tools": route_cfg.get("max_parallel_tools"),
                },
            }
        )
    out["route_decision"] = route_decision
    return role, cls, model, out


def dispatch(task: Dict[str, str], ui_model: str | None = None):
    """Dispatch ``task`` to the appropriate agent instance.

    The task's ``role`` is normalised via ``ALIASES`` and ``ROLE_SYNONYMS``
    before lookup.  Unknown roles fall back to ``Research Scientist``.  If the
    resolved agent lacks a callable interface, a single warning is logged and the
    task is rerouted to ``Research Scientist``.
    """

    role = canonicalize(_alias(task.get("role")))
    if role:
        role = ROLE_SYNONYMS.get(role, role)
    canonical = role if role in AGENT_REGISTRY else "Research Scientist"

    model = select_model("agent", ui_model, agent_name=canonical)
    meta = {"purpose": "agent", "agent": canonical, "role": task.get("role")}
    agent = get_agent(canonical)
    try:
        return invoke_agent(agent, task=task, model=model, meta=meta)
    except TypeError as e:
        if canonical != "Research Scientist":
            logger.warning("Uncallable agent %s: %s", canonical, e)
            fb = get_agent("Research Scientist")
            fb_model = select_model("agent", ui_model, agent_name="Research Scientist")
            fb_meta = {**meta, "agent": "Research Scientist", "fallback_from": canonical}
            return invoke_agent(fb, task=task, model=fb_model, meta=fb_meta)
        raise


__all__ = [
    "choose_agent_for_task",
    "KEYWORDS",
    "ALIASES",
    "ROLE_SYNONYMS",
    "route_task",
    "dispatch",
]
