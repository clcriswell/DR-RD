from agents.base_agent import LLMRoleAgent


class ReflectionAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("Reflection", model)
