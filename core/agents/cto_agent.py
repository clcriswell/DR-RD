from __future__ import annotations

import json
from typing import Any

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.tool_use import should_use_tool
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class CTOAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        tool_req = should_use_tool(task) if isinstance(task, dict) else None
        tool_result = None
        if tool_req:
            try:
                out = self.run_tool(tool_req["tool"], tool_req.get("params", {}))
                tool_result = {"output": out}
            except Exception as e:  # pragma: no cover - best effort
                tool_result = {"error": str(e)}
        spec = {
            "role": "CTO",
            "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            "inputs": {
                "idea": idea,
                "task": task.get("description", "") if isinstance(task, dict) else str(task or ""),
            },
            "io_schema_ref": "dr_rd/schemas/cto_v2.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "technical strategy",
            "evaluation_hooks": ["self_check_minimal"],
        }
        result = super().run_with_spec(spec, **kwargs)
        if tool_result:
            try:
                data = json.loads(result)
                data["tool_result"] = tool_result
                result = json.dumps(data)
            except Exception:  # pragma: no cover
                pass
        return result
