from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class FinanceAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        text = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "Finance",
            "task": text,
            "inputs": prepare_prompt_inputs(task),
            "io_schema_ref": "dr_rd/schemas/finance_v2.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "budgeting and costs",
            "evaluation_hooks": ["self_check_minimal"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
