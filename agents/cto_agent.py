from agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are the Chief Technology Officer with deep technical expertise and strategic vision. "
    "Provide high-level architecture and technical direction."
)

class CTOAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
