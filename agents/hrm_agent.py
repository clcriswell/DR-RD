from agents.base_agent import LLMRoleAgent


class HRMAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("HRM", model)
