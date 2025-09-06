from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class HRMAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        spec = {
            "role": "HRM",
            "task": str(task or ""),
            "inputs": {"idea": idea, "task": str(task or "")},
            "io_schema_ref": "dr_rd/schemas/hrm_v2.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "role mapping",
            "evaluation_hooks": ["self_check_minimal"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
