from core.agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are an HR Manager specializing in R&D projects. "
    "Identify the expert roles needed for the following idea."
)

class HRMAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
