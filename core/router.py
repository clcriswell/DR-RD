"""Simple task-to-agent routing utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import streamlit as st
import yaml

from config import feature_flags
from core.agents.invoke import invoke_agent
from core.agents.unified_registry import AGENT_REGISTRY, get_agent
from core.llm import select_model
from core.roles import canonicalize
from dr_rd.config.env import get_env
from dr_rd.telemetry import metrics
from utils.telemetry import tasks_routed

logger = logging.getLogger(__name__)
BUDGETS: dict[str, Any] | None = None
RAG_CFG = (
    yaml.safe_load(Path("config/rag.yaml").read_text()) if Path("config/rag.yaml").exists() else {}
)


def _load_budgets() -> dict[str, Any]:
    global BUDGETS
    if BUDGETS is None:
        cfg_path = Path(__file__).resolve().parents[1] / "config" / "budgets.yaml"
        with open(cfg_path, encoding="utf-8") as fh:
            BUDGETS = yaml.safe_load(fh) or {}
    profile = feature_flags.BUDGET_PROFILE
    return BUDGETS.get(profile, {})


# ---------------------------------------------------------------------------
# Lightweight keyword heuristics
# ---------------------------------------------------------------------------
# Map lowercase keywords to the canonical role they imply.  This dictionary is
# intentionally small; it only covers a few common business domains and can be
# extended as needed.
KEYWORDS: dict[str, str] = {
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
ALIASES: dict[str, str] = {
    "manufacturing technician": "Research Scientist",
    "quantum physicist": "Research Scientist",
    "physicist": "Research Scientist",
    "researcher": "Research Scientist",
    "scientist": "Research Scientist",
    "engineer": "CTO",
    "software developer": "CTO",
    "software engineer": "CTO",
    "developer": "CTO",
    "product designer": "Research Scientist",
    "quality analyst": "QA",
    "qa": "QA",
    "quality assurance": "QA",
    "dev": "CTO",
    "mkt": "Marketing Analyst",
}


ROLE_SYNONYMS: dict[str, str] = {
    "Project Manager": "Planner",
    "project manager": "Planner",
    "Program Manager": "Planner",
    "program manager": "Planner",
    "Product Manager": "Planner",
    "product manager": "Planner",
    "Risk Manager": "Regulatory",
    "risk manager": "Regulatory",
    "Software Developer": "CTO",
    "Engineer": "CTO",
    "Developer": "CTO",
    "Quality Analyst": "QA",
    "Marketing": "Marketing Analyst",
}


def _alias(role: str | None) -> str | None:
    if not role:
        return role
    r = role.strip()
    low = r.lower()
    for prefix in ("dev_", "qa_", "mkt_"):
        if low.startswith(prefix):
            low = prefix[:-1]
            return ALIASES.get(low, low)
    return ALIASES.get(low, r)


def choose_agent_for_task(
    planned_role: str | None,
    title: str,
    description: str | None,
    summary: str | None = None,
    ui_model: str | None = None,
    task: dict[str, str] | None = None,
) -> tuple[str, type, str]:
    """Return the canonical role, agent class, and model for a task."""

    _routing_text = f"{title} {(task.get('description') or task.get('summary') or '')}".strip()
    role = canonicalize(_alias(planned_role))
    if role:
        role = ROLE_SYNONYMS.get(role, role)
    if not role or role not in AGENT_REGISTRY:
        model = select_model("agent", ui_model, agent_name="Dynamic Specialist")
        return "Dynamic Specialist", AGENT_REGISTRY["Dynamic Specialist"], model
    model = select_model("agent", ui_model, agent_name=role)
    return role, AGENT_REGISTRY[role], model


def route_task(
    task: dict[str, str], ui_model: str | None = None
) -> tuple[str, type, str, dict[str, str]]:
    """Resolve role/agent for a task dict without dropping fields."""
    planned = task.get("role")
    if task.get("hints", {}).get("simulation_domain"):
        planned = "Simulation"
    desc = task.get("description")
    summary = task.get("summary")
    role, cls, model = choose_agent_for_task(
        planned, task.get("title", ""), desc, summary, ui_model, task
    )
    out = dict(task)
    out["role"] = role
    out.setdefault("stop_rules", task.get("stop_rules", []))

    route_decision: dict[str, Any] = {"selected_role": role}
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
                "dense_enabled": bool(get_env("OPENAI_API_KEY")),
                "caps": {
                    "max_tool_calls": exec_cfg.get("max_tool_calls"),
                    "max_parallel_tools": route_cfg.get("max_parallel_tools"),
                },
            }
        )
    out["route_decision"] = route_decision
    metrics.inc(
        "route_decision",
        role=role,
        retrieval_level=str(route_decision.get("retrieval_level")),
        caps=json.dumps(route_decision.get("caps", {})),
    )
    tasks_routed(1)
    try:
        st.session_state.setdefault("routing_report", []).append(
            {
                "task_id": task.get("id"),
                "planned_role": planned,
                "routed_role": role,
                "model": model,
            }
        )
    except Exception:
        pass
    return role, cls, model, out


def dispatch(task: dict[str, str], ui_model: str | None = None):
    """Dispatch ``task`` to the appropriate agent instance.

    The task's ``role`` is normalised via ``ALIASES`` and ``ROLE_SYNONYMS``
    before lookup.  Unknown roles fall back to ``Dynamic Specialist``.  If the
    resolved agent lacks a callable interface, a single warning is logged and the
    task is rerouted to ``Dynamic Specialist``.
    """

    role = canonicalize(_alias(task.get("role")))
    if role:
        role = ROLE_SYNONYMS.get(role, role)
    canonical = role if role in AGENT_REGISTRY else "Dynamic Specialist"

    model = select_model("agent", ui_model, agent_name=canonical)
    meta = {"purpose": "agent", "agent": canonical, "role": task.get("role")}
    agent = get_agent(canonical)
    try:
        return invoke_agent(agent, task=task, model=model, meta=meta)
    except TypeError as e:
        if canonical != "Dynamic Specialist":
            logger.warning("Uncallable agent %s: %s", canonical, e)
            fb = get_agent("Dynamic Specialist")
            fb_model = select_model("agent", ui_model, agent_name="Dynamic Specialist")
            fb_meta = {**meta, "agent": "Dynamic Specialist", "fallback_from": canonical}
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
