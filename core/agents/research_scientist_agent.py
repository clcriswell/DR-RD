import json
from core.agents.base_agent import LLMRoleAgent
from core.agents.tool_use import should_use_tool


class ResearchScientistAgent(LLMRoleAgent):
    def act(self, idea, task=None, **kwargs) -> str:
        tool_req = should_use_tool(task) if isinstance(task, dict) else None
        tool_result = None
        if tool_req:
            if tool_req.get("tool") == "apply_patch":
                tool_result = {"error": "apply_patch not permitted"}
            else:
                try:
                    out = self.run_tool(tool_req["tool"], tool_req.get("params", {}))
                    tool_result = {"output": out}
                except Exception as e:
                    tool_result = {"error": str(e)}
        if isinstance(task, dict):
            system_prompt = (
                "You are the Research Scientist. Provide specific, non-generic analysis with concrete details. "
                "Conclude with a JSON summary using keys: role, task, findings, risks, next_steps, sources."
            )
            user_prompt = (
                f"Project Idea:\n{idea}\n\n"
                f"Task Title:\n{task.get('title','')}\n\n"
                f"Task Description:\n{task.get('description','')}"
            )
            result = super().act(system_prompt, user_prompt, **kwargs)
        else:
            result = super().act(idea, task or "", **kwargs)
        if tool_result:
            try:
                data = json.loads(result)
                data["tool_result"] = tool_result
                result = json.dumps(data)
            except Exception:
                pass
        return result
