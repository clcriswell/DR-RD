from agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are a Research Scientist with deep literature awareness. "
    "Provide specific, non-generic analysis with concrete details."
)

class ResearchScientistAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
