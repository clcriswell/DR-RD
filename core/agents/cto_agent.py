from __future__ import annotations

from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from core.agents.tool_use import should_use_tool
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class CTOAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        tool_req = should_use_tool(task) if isinstance(task, dict) else None
        if tool_req:
            try:
                self.run_tool(tool_req["tool"], tool_req.get("params", {}))
            except Exception:  # pragma: no cover - best effort
                pass
        text = task.get("description", "") if isinstance(task, dict) else str(task or "")
        spec = {
            "role": "CTO",
            "task": text,
            "inputs": prepare_prompt_inputs(task, idea=idea),
            "io_schema_ref": "dr_rd/schemas/cto_v2.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "technical strategy",
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
        }
        result = super().run_with_spec(spec, **kwargs)
        return result
