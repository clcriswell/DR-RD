from agents.base_agent import LLMRoleAgent


class RegulatorySpecialistAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("RegulatorySpecialist", model)
