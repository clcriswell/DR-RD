from __future__ import annotations

import json
from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class ReflectionAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        task_str = task if isinstance(task, str) else json.dumps(task or "")

        def _has_placeholder(obj: Any) -> bool:
            if isinstance(obj, str):
                return obj.strip() == "" or obj.strip() == "Not determined"
            if isinstance(obj, list):
                return any(_has_placeholder(v) for v in obj)
            if isinstance(obj, dict):
                return any(_has_placeholder(v) for v in obj.values()) or obj == {}
            return obj in (None, "")

        try:
            data = json.loads(task_str) if task_str else {}
        except Exception:
            data = {}

        if not any(_has_placeholder(v) for v in data.values()):
            return "no further tasks"

        inputs = prepare_prompt_inputs(task)
        inputs.setdefault("task_payload", task_str)
        spec = {
            "role": "Reflection",
            "task": task_str,
            "inputs": inputs,
            "io_schema_ref": "dr_rd/schemas/reflection_v1.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "self critique",
            "evaluation_hooks": ["self_check_minimal", "placeholder_check"],
        }
        return super().run_with_spec(spec, **kwargs)

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)
