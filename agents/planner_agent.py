from agents.base_agent import LLMRoleAgent
from dr_rd.utils.llm_client import llm_call
from config.feature_flags import EVALUATOR_MIN_OVERALL
import json
import openai
import re

ROLE_PROMPT = (
    "You are a Project Planner AI. Decompose the given idea into specific tasks, "
    "noting the domain or role needed for each task. Return JSON with a 'tasks' array "
    "where each item has 'role', 'title', and 'description'."
)

class PlannerAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)

    def run(self, idea: str, task: str, difficulty: str = "normal", roles: list[str] | None = None):
        """Call the model to produce a task plan and return it as a dict."""
        roles_section = ""
        if roles:
            roles_lines = "\n".join(f"- {r}" for r in roles)
            roles_section = (
                "Specialist roles to include (use exactly these when suitable; add truly missing ones if critical):\n"
                f"{roles_lines}\n"
            )
        user_prompt = (
            f"Project Idea: {idea}\nTask: {task}\n{roles_section}"
            "Output JSON tasks with a 'role', 'title', and 'description' field."
        )
        params = {}
        if "4o" in self.model:
            params["response_format"] = {"type": "json_object"}
        response = llm_call(
            openai,
            self.model,
            stage="plan",
            messages=[
                {"role": "system", "content": ROLE_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            **params,
        )
        text = response.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pairs = re.findall(r'"([^"\\]+)"\s*:\s*"([^"\\]+)"', text)
            return {k: v for k, v in pairs}

    def revise_plan(self, workspace: dict):
        """Revise an existing plan based on evaluator feedback."""
        user_prompt = json.dumps(workspace)
        params = {}
        if "4o" in self.model:
            params["response_format"] = {"type": "json_object"}
        response = llm_call(
            openai,
            self.model,
            stage="plan",
            messages=[
                {"role": "system", "content": ROLE_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            **params,
        )
        text = response.choices[0].message.content.strip()
        try:
            data = json.loads(text)
            tasks = data.get("updated_tasks", [])
        except json.JSONDecodeError:
            tasks = []
        if workspace.get("scorecard", {}).get("overall", 1.0) < EVALUATOR_MIN_OVERALL:
            tasks.append({"task": "Improve plan to address deficiencies", "role": self.name})
        return tasks
