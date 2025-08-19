from agents.base_agent import LLMRoleAgent

GENERIC_SYSTEM_FMT = """You are a world-class {role}. 
Respond ONLY with structured JSON as instructed by the task contract. 
Bring deep domain knowledge for {role} and cite sources if available."""

class GenericDomainAgent(LLMRoleAgent):
    def __init__(self, role: str, model: str):
        super().__init__(role, model)
        self.role = role

    def act(self, idea, task=None, **kwargs) -> str:
        if isinstance(task, dict):
            system_prompt = GENERIC_SYSTEM_FMT.format(role=self.role)
            user_prompt = (
                f"Project Idea:\n{idea}\n\n"
                f"Task Title:\n{task.get('title','')}\n\n"
                f"Task Description:\n{task.get('description','')}"
            )
            return super().act(system_prompt, user_prompt, **kwargs)
        return super().act(idea, task or "", **kwargs)
