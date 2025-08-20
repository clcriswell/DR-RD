from core.agents.base_agent import LLMRoleAgent


class ResearchScientistAgent(LLMRoleAgent):
    def act(self, idea, task=None, **kwargs) -> str:
        if isinstance(task, dict):
            system_prompt = (
                "You are the Research Scientist. Provide specific, non-generic analysis with concrete details."
            )
            user_prompt = (
                f"Project Idea:\n{idea}\n\n"
                f"Task Title:\n{task.get('title','')}\n\n"
                f"Task Description:\n{task.get('description','')}"
            )
            return super().act(system_prompt, user_prompt, **kwargs)
        return super().act(idea, task or "", **kwargs)
