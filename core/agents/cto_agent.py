from core.agents.base_agent import LLMRoleAgent
from prompts.prompts import CTO_SYSTEM_PROMPT, CTO_USER_PROMPT_TEMPLATE


class CTOAgent(LLMRoleAgent):
    def act(self, idea, task=None, **kwargs) -> str:
        if isinstance(task, dict):
            system_prompt = CTO_SYSTEM_PROMPT
            user_prompt = CTO_USER_PROMPT_TEMPLATE.format(
                idea=idea,
                title=task.get("title", ""),
                description=task.get("description", ""),
            )
            return super().act(system_prompt, user_prompt, **kwargs)
        return super().act(idea, task or "", **kwargs)
