from core.agents.base_agent import LLMRoleAgent


class CTOAgent(LLMRoleAgent):
    def act(self, idea, task=None, **kwargs) -> str:
        if isinstance(task, dict):
            system_prompt = (
                "You are the CTO. Assess feasibility, architecture, and risks. Return clear, structured guidance."
            )
            user_prompt = (
                f"Project Idea:\n{idea}\n\n"
                f"Task Title:\n{task.get('title','')}\n\n"
                f"Task Description:\n{task.get('description','')}"
            )
            return super().act(system_prompt, user_prompt, **kwargs)
        return super().act(idea, task or "", **kwargs)
