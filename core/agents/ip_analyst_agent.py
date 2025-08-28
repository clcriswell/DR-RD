from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from config import feature_flags
from core.agents.prompt_agent import PromptFactoryAgent
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class IPAnalystAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        budgets_path = Path(__file__).resolve().parents[2] / "config" / "budgets.yaml"
        with open(budgets_path, "r", encoding="utf-8") as fh:
            budgets = yaml.safe_load(fh) or {}
        top_k = budgets.get(feature_flags.BUDGET_PROFILE, {}).get("exec", {}).get("top_k", 5)
        spec = {
            "role": "IP Analyst",
            "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            "inputs": {
                "idea": idea,
                "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            },
            "io_schema_ref": "dr_rd/schemas/patent_evidence_v1.json",
            "retrieval_policy": RetrievalPolicy.AGGRESSIVE,
            "top_k": top_k,
            "capabilities": "prior art search",
            "evaluation_hooks": ["patent_overlap_check"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
