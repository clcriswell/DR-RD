from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class MechanicalSystemsLeadAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        text = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "Mechanical Systems Lead",
            "task": text,
            "inputs": prepare_prompt_inputs(task, idea=idea),
            "io_schema_ref": "dr_rd/schemas/mechanical_systems_lead_v1.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "mechanical design",
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
