from core.agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are a Regulatory Compliance Specialist. "
    "Review the idea for regulatory or safety requirements and highlight compliance issues."
)

class RegulatorySpecialistAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
