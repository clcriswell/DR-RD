from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict
from .base_agent import Agent

from .cto_agent import CTOAgent
from .scientist_agent import ResearchScientistAgent
from .regulatory_agent import RegulatoryAgent
from .finance_agent import FinanceAgent

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "modes.yaml"


def load_mode_models(mode: str | None = None) -> Dict[str, str]:
    mode = (mode or os.getenv("DRRD_MODE", "test")).lower()
    with open(CONFIG_PATH) as fh:
        data = json.load(fh)
    return data.get(mode, data.get("test", {}))


def build_agents(mode: str | None = None) -> Dict[str, Agent]:
    models = load_mode_models(mode)
    default = models.get("default", "gpt-3.5-turbo")
    return {
        "CTO": CTOAgent(model_id=models.get("CTO", default)),
        "Research": ResearchScientistAgent(model_id=models.get("Research", default)),
        "Regulatory": RegulatoryAgent(model_id=models.get("Regulatory", default)),
        "Finance": FinanceAgent(model_id=models.get("Finance", default)),
    }


AGENTS = build_agents()

_KEYWORDS = {
    "CTO": ["architecture", "risk", "scalability"],
    "Research": ["materials", "physics", "prior art", "literature"],
    "Regulatory": ["compliance", "fda", "iso", "fcc"],
    "Finance": ["cost", "bom", "budget"],
}


def get_agent_for_task(task: str, agents: Dict[str, Agent] | None = None) -> Agent:
    agents = agents or AGENTS
    text = (task or "").lower()
    for name, words in _KEYWORDS.items():
        for w in words:
            if w in text:
                return agents[name]
    return agents["Research"]
