from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy

COMPLIANCE_KEYWORDS = ["compliance", "cfr", "docket", "regulations.gov"]


class RegulatoryAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        text = ""
        if isinstance(task, dict):
            text = f"{task.get('description', '')} {task.get('role', '')}"
        else:
            text = str(task or "")
        policy = RetrievalPolicy.LIGHT
        if any(k in text.lower() for k in COMPLIANCE_KEYWORDS):
            policy = RetrievalPolicy.AGGRESSIVE
        base_task = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "Regulatory",
            "task": base_task,
            "inputs": prepare_prompt_inputs(task),
            "io_schema_ref": "dr_rd/schemas/regulatory_v2.json",
            "retrieval_policy": policy,
            "capabilities": "compliance analysis",
            "evaluation_hooks": ["compartment_check", "reg_citation_check"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
