from __future__ import annotations

from typing import Dict, Tuple
from .base_agent import Agent

from .cto_agent import CTOAgent
from .research_scientist_agent import ResearchScientistAgent
from .regulatory_agent import RegulatoryAgent
from .finance_agent import FinanceAgent
from core.agents.marketing_agent import MarketingAgent
from core.agents.ip_analyst_agent import IPAnalystAgent
from config.agent_models import AGENT_MODEL_MAP

DEFAULT_EXEC_MODEL = AGENT_MODEL_MAP.get("Research", "gpt-5")
AGENT_MODEL_MAP.setdefault(
    "Marketing Analyst", AGENT_MODEL_MAP.get("Research", DEFAULT_EXEC_MODEL)
)
AGENT_MODEL_MAP.setdefault(
    "IP Analyst", AGENT_MODEL_MAP.get("Research", DEFAULT_EXEC_MODEL)
)


def build_agents(mode: str | None = None, models: Dict | None = None) -> Dict[str, Agent]:
    """Build the core advisory core.agents.

    If ``models`` is supplied (typically from ``config/modes.yaml"), its
    ``exec`` entry is used as the default model for all execution-stage agents
    (CTO, Research, Regulatory, Finance, Marketing Analyst, IP Analyst).
    This allows per-mode model assignments while still falling back to
    ``config/agent_models.py`` when unspecified.
    """

    exec_default = (models or {}).get("exec") or AGENT_MODEL_MAP.get(
        "Research", DEFAULT_EXEC_MODEL
    )

    def _m(role: str) -> str:
        if models and role in {
            "CTO",
            "Research",
            "Regulatory",
            "Finance",
            "Marketing Analyst",
            "IP Analyst",
        }:
            return models.get("exec", exec_default)
        return AGENT_MODEL_MAP.get(role, exec_default)

    return {
        "CTO": CTOAgent(_m("CTO")),
        "Research": ResearchScientistAgent(_m("Research")),
        "Regulatory": RegulatoryAgent(_m("Regulatory")),
        "Finance": FinanceAgent(_m("Finance")),
        "Marketing Analyst": MarketingAgent(_m("Marketing Analyst")),
        "IP Analyst": IPAnalystAgent(_m("IP Analyst")),
    }


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
    "Research": [],
}


def choose_agent_for_task(
    planned_role: str | None, title: str, agents: Dict[str, Agent]
) -> Tuple[str, Agent]:
    # 1) Exact role match
    if planned_role and planned_role in agents:
        return planned_role, agents[planned_role]
    # 2) Keyword fallback
    t = (title or "").lower()
    for role_key, words in KEYWORDS.items():
        if role_key in agents and any(w in t for w in words):
            return role_key, agents[role_key]
    # 3) Safe default
    fallback = core.agents.get("Research") or next(iter(core.agents.values()))
    return "Research", fallback


def get_agent_for_task(task: str, agents: Dict[str, Agent] | None = None) -> Agent:
    _, agent = choose_agent_for_task(None, task, agents or AGENTS)
    return agent

# --- Added: mode-aware model loader that also installs the BudgetManager ---
def load_mode_models(mode: str | None = None) -> dict:
    """
    Load per-mode model assignments from config/modes.yaml, install the BudgetManager
    so dr_rd.utils.llm_client enforces caps, and expose a simple mapping used by
    core.orchestrator.
    """
    import streamlit as st
    from app.config_loader import load_mode
    from dr_rd.utils.llm_client import set_budget_manager

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
        "Planner": m.get("plan", "gpt-5"),
        "exec": m.get("exec", m.get("plan", "gpt-5")),
        "synth": m.get("synth", m.get("exec", "gpt-5")),
        "default": m.get("exec", m.get("plan", "gpt-5")),
    }
