from agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are a Project Planner AI. Decompose the given idea into specific tasks, "
    "noting the domain or role needed for each task."
)

class PlannerAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
