from __future__ import annotations

"""Central registry for all concrete agent classes.

This module exposes a mapping from canonical role names to their implementing
classes. Other parts of the system can look up agent classes here instead of
maintaining ad-hoc registries.
"""

from typing import Dict, Tuple, Type, Optional

from .base_agent import LLMRoleAgent as BaseAgent

from .cto_agent import CTOAgent
from .research_scientist_agent import ResearchScientistAgent
from .regulatory_agent import RegulatoryAgent
from .finance_agent import FinanceAgent
from .marketing_agent import MarketingAgent
from .ip_analyst_agent import IPAnalystAgent
from .planner_agent import PlannerAgent
from .synthesizer_agent import SynthesizerAgent
from config.agent_models import AGENT_MODEL_MAP

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
}


def get_agent_class(role: str) -> Optional[Type[BaseAgent]]:
    """Return the agent class for ``role`` if registered."""

    return AGENT_REGISTRY.get(role)


# ---------------------------------------------------------------------------
# Factory utilities for creating commonly used agent instances
# ---------------------------------------------------------------------------

DEFAULT_EXEC_MODEL = AGENT_MODEL_MAP.get("Research Scientist", "gpt-4.1-mini")
AGENT_MODEL_MAP.setdefault(
    "Marketing Analyst", AGENT_MODEL_MAP.get("Research Scientist", DEFAULT_EXEC_MODEL)
)
AGENT_MODEL_MAP.setdefault(
    "IP Analyst", AGENT_MODEL_MAP.get("Research Scientist", DEFAULT_EXEC_MODEL)
)


def build_agents(mode: str | None = None, models: Dict | None = None) -> Dict[str, BaseAgent]:
    """Instantiate the standard execution-stage agents.

    ``models`` may supply per-role model overrides; otherwise ``AGENT_MODEL_MAP``
    and ``DEFAULT_EXEC_MODEL`` are consulted.
    """

    exec_default = (models or {}).get("exec") or AGENT_MODEL_MAP.get(
        "Research Scientist", DEFAULT_EXEC_MODEL
    )

    def _m(role: str) -> str:
        if models and role in {
            "CTO",
            "Research Scientist",
            "Regulatory",
            "Finance",
            "Marketing Analyst",
            "IP Analyst",
        }:
            return models.get("exec", exec_default)
        return AGENT_MODEL_MAP.get(role, exec_default)

    agents: Dict[str, BaseAgent] = {}
    for role in [
        "CTO",
        "Research Scientist",
        "Regulatory",
        "Finance",
        "Marketing Analyst",
        "IP Analyst",
    ]:
        cls = get_agent_class(role)
        if cls:
            agents[role] = cls(_m(role))
    return agents


AGENTS = build_agents()

KEYWORDS = {
    "Marketing Analyst": [
        "market",
        "customer",
        "user",
        "segment",
        "tam",
        "sam",
        "som",
        "gtm",
        "competition",
        "competitor",
        "competitive",
        "pricing",
        "price",
        "revenue",
        "sales",
        "adoption",
        "roi",
    ],
    "IP Analyst": [
        "patent",
        "prior art",
        "intellectual property",
        "claims",
        "novelty",
        "patentability",
        "fto",
        "freedom to operate",
        "ip strategy",
    ],
    "Finance": [
        "budget",
        "cost",
        "bom",
        "bill of materials",
        "capex",
        "opex",
        "unit economics",
        "breakeven",
        "payback",
        "roi",
    ],
    "Regulatory": ["regulatory", "compliance", "fda", "ce", "iso", "510(k)", "hipaa", "gdpr"],
    "CTO": ["architecture", "system design", "tech strategy", "roadmap"],
    "Research Scientist": [],
}


def choose_agent_for_task(
    planned_role: str | None, title: str, agents: Dict[str, BaseAgent]
) -> Tuple[str, BaseAgent]:
    # 1) Exact role match
    if planned_role and planned_role in agents:
        return planned_role, agents[planned_role]
    # 2) Keyword fallback
    t = (title or "").lower()
    for role_key, words in KEYWORDS.items():
        if role_key in agents and any(w in t for w in words):
            return role_key, agents[role_key]
    # 3) Safe default
    fallback = agents.get("Research Scientist") or next(iter(agents.values()))
    return "Research Scientist", fallback


def get_agent_for_task(task: str, agents: Dict[str, BaseAgent] | None = None) -> BaseAgent:
    _, agent = choose_agent_for_task(None, task, agents or AGENTS)
    return agent

# --- Added: mode-aware model loader that also installs the BudgetManager ---
def load_mode_models(mode: str | None = None) -> dict:
    """
    Load per-mode model assignments from config/modes.yaml, install the BudgetManager
    so core.llm_client enforces caps, and expose a simple mapping used by
    core.orchestrator.
    """
    import streamlit as st
    from app.config_loader import load_mode
    from core.llm_client import set_budget_manager

    # Default to deep reasoning profile when no mode is specified
    mode = mode or "deep"
    mode_cfg, budget = load_mode(mode)

    # Share mode config with callers that read st.session_state
    try:
        st.session_state["MODE_CFG"] = mode_cfg
    except Exception:
        pass

    set_budget_manager(budget)
    m = (mode_cfg or {}).get("models", {}) or {}
    # Rebuild global agents using mode-specific exec model
    global AGENTS
    AGENTS = build_agents(mode, models=m)
    # Map planner/synth plus sensible defaults for exec/default
    return {
        "Planner": m.get("plan", "gpt-4.1-mini"),
        "exec": m.get("exec", m.get("plan", "gpt-4.1-mini")),
        "synth": m.get("synth", m.get("exec", "gpt-4.1-mini")),
        "default": m.get("exec", m.get("plan", "gpt-4.1-mini")),
    }
