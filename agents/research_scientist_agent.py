from agents.base_agent import LLMRoleAgent


class ResearchScientistAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("ResearchScientist", model)
