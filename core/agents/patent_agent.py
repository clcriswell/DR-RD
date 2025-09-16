from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class PatentAgent(PromptFactoryAgent):
    """Patent Agent for intellectual property and patentability analysis."""

    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        text = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "Patent",
            "task": text,
            "inputs": prepare_prompt_inputs(task),
            "io_schema_ref": "dr_rd/schemas/generic_v2.json",
            "retrieval_policy": RetrievalPolicy.AGGRESSIVE,
            "capabilities": "patent analysis",
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
