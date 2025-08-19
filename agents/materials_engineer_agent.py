from agents.base_agent import LLMRoleAgent

ROLE_PROMPT = (
    "You are a Materials Engineer specialized in material selection and engineering feasibility. "
    "Evaluate material choices and manufacturing considerations."
)

class MaterialsEngineerAgent(LLMRoleAgent):
    def act(self, system_prompt: str = ROLE_PROMPT, user_prompt: str = "", **kwargs) -> str:
        return super().act(system_prompt, user_prompt, **kwargs)
