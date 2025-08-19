from agents.base_agent import LLMRoleAgent


class MaterialsEngineerAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("MaterialsEngineer", model)
