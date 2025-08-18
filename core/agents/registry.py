from __future__ import annotations

from typing import Dict, Tuple
from .base_agent import Agent

from .cto_agent import CTOAgent
from .scientist_agent import ResearchScientistAgent
from .regulatory_agent import RegulatoryAgent
from .finance_agent import FinanceAgent
from agents.marketing_agent import MarketingAgent
from agents.ip_analyst_agent import IPAnalystAgent
from config.agent_models import AGENT_MODEL_MAP

DEFAULT_EXEC_MODEL = AGENT_MODEL_MAP.get("Research", "gpt-3.5-turbo")
AGENT_MODEL_MAP.setdefault(
    "Marketing Analyst", AGENT_MODEL_MAP.get("Research", DEFAULT_EXEC_MODEL)
)
AGENT_MODEL_MAP.setdefault(
    "IP Analyst", AGENT_MODEL_MAP.get("Research", DEFAULT_EXEC_MODEL)
)


def build_agents(mode: str | None = None) -> Dict[str, Agent]:
    """Build the core advisory agents.

    The previous implementation loaded per-mode model assignments from
    ``config/modes.yaml``. With the introduction of budget-aware modes, that
    file now tracks cost caps rather than agent models. To keep tests stable
    and avoid coupling agent selection to budget configuration, this registry
    now relies on the static mapping defined in ``config/agent_models.py``.

    The ``mode`` argument is preserved for backward compatibility but is
    currently ignored.
    """

    default = AGENT_MODEL_MAP.get("Research", DEFAULT_EXEC_MODEL)
    return {
        "CTO": CTOAgent(model_id=AGENT_MODEL_MAP.get("CTO", default)),
        "Research": ResearchScientistAgent(model_id=AGENT_MODEL_MAP.get("Research", default)),
        "Regulatory": RegulatoryAgent(model_id=AGENT_MODEL_MAP.get("Regulatory", default)),
        "Finance": FinanceAgent(model_id=AGENT_MODEL_MAP.get("Finance", default)),
        "Marketing Analyst": MarketingAgent(model=AGENT_MODEL_MAP.get("Marketing Analyst", default)),
        "IP Analyst": IPAnalystAgent(model=AGENT_MODEL_MAP.get("IP Analyst", default)),
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
) -> Tuple[Agent, str]:
    # 1) Exact role match
    if planned_role and planned_role in agents:
        return agents[planned_role], planned_role
    # 2) Keyword fallback
    t = (title or "").lower()
    for role_key, words in KEYWORDS.items():
        if role_key in agents and any(w in t for w in words):
            return agents[role_key], role_key
    # 3) Safe default
    fallback = agents.get("Research") or next(iter(agents.values()))
    return fallback, "Research"


def get_agent_for_task(task: str, agents: Dict[str, Agent] | None = None) -> Agent:
    agent, _ = choose_agent_for_task(None, task, agents or AGENTS)
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

    mode = mode or "test"
    mode_cfg, budget = load_mode(mode)

    # Share mode config with callers that read st.session_state
    try:
        st.session_state["MODE_CFG"] = mode_cfg
    except Exception:
        pass

    set_budget_manager(budget)
    m = (mode_cfg or {}).get("models", {}) or {}
    # Map planner/synth plus sensible defaults for exec/default
    return {
        "Planner": m.get("plan", "gpt-3.5-turbo"),
        "exec": m.get("exec", m.get("plan", "gpt-3.5-turbo")),
        "synth": m.get("synth", m.get("exec", "gpt-3.5-turbo")),
        "default": m.get("exec", m.get("plan", "gpt-3.5-turbo")),
    }
