from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class MarketingAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        spec = {
            "role": "Marketing Analyst",
            "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            "inputs": {
                "idea": idea,
                "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            },
            "io_schema_ref": "dr_rd/schemas/marketing_v1.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "market analysis",
            "evaluation_hooks": ["self_check_minimal"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
