from agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are the Chief Scientist overseeing this project. "
    "Integrate all contributions into a comprehensive R&D plan."
)

class ChiefScientistAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
