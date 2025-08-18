from __future__ import annotations

from typing import Dict
from .base_agent import Agent

from .cto_agent import CTOAgent
from .scientist_agent import ResearchScientistAgent
from .regulatory_agent import RegulatoryAgent
from .finance_agent import FinanceAgent
from agents.marketing_agent import MarketingAgent
from agents.ip_analyst_agent import IPAnalystAgent
from config.agent_models import AGENT_MODEL_MAP


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

    default = AGENT_MODEL_MAP.get("Research", "gpt-3.5-turbo")
    return {
        "CTO": CTOAgent(model_id=AGENT_MODEL_MAP.get("CTO", default)),
        "Research": ResearchScientistAgent(model_id=AGENT_MODEL_MAP.get("Research", default)),
        "Regulatory": RegulatoryAgent(model_id=AGENT_MODEL_MAP.get("Regulatory", default)),
        "Finance": FinanceAgent(model_id=AGENT_MODEL_MAP.get("Finance", default)),
        "Marketing Analyst": MarketingAgent(model=AGENT_MODEL_MAP.get("Marketing", default)),
        "IP Analyst": IPAnalystAgent(model=AGENT_MODEL_MAP.get("IP", default)),
    }


AGENTS = build_agents()

_KEYWORDS = {
    "CTO": ["architecture", "risk", "scalability"],
    "Research": ["materials", "physics", "prior art", "literature"],
    "Regulatory": ["compliance", "fda", "iso", "fcc"],
    "Finance": [
        "cost",
        "bom",
        "budget",
        "bill of materials",
        "unit economics",
        "capex",
        "opex",
        "payback",
        "breakeven",
        "roi",
    ],
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
}


def get_agent_for_task(task: str, agents: Dict[str, Agent] | None = None) -> Agent:
    agents = agents or AGENTS
    text = (task or "").lower()
    for name, words in _KEYWORDS.items():
        for w in words:
            if w in text:
                return agents[name]
    return agents["Research"]

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
