from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class MaterialsEngineerAgent(PromptFactoryAgent):
    """Prompt-based agent for materials tasks with a simple call signature."""

    def __call__(self, task: Any, model: str | None = None, meta: dict | None = None) -> str:
        text = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "Materials Engineer",
            "task": text,
            "inputs": prepare_prompt_inputs(task),
            "io_schema_ref": "dr_rd/schemas/materials_engineer_v2.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "materials selection",
            "evaluation_hooks": ["self_check_minimal"],
        }
        return super().run_with_spec(spec, model=model)

    def run(self, task: Any, model: str) -> str:  # pragma: no cover - compatibility
        return self.__call__(task, model=model)
