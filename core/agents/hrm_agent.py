from core.agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
# Schema: dr_rd/schemas/hrm_agent.json
    "You are an HR Manager specializing in R&D projects. "
    "Identify the expert roles needed for the following idea. "
    "Conclude with a JSON summary using keys: role, task, findings, risks, next_steps, sources."
)

class HRMAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
