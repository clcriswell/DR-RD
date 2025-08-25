from core.agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are a Reflection agent analyzing the team's outputs. "
    "Determine if follow-up tasks are required. Respond with either a JSON array of follow-up task strings or the exact string 'no further tasks'."
)

class ReflectionAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
