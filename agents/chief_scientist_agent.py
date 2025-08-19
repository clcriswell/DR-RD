from agents.base_agent import LLMRoleAgent


class ChiefScientistAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("ChiefScientist", model)
