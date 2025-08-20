from core.agents.base_agent import BaseAgent
from prompts.prompts import (
    REGULATORY_SYSTEM_PROMPT,
    REGULATORY_USER_PROMPT_TEMPLATE,
)

"""Regulatory Agent for compliance and standards analysis."""
class RegulatoryAgent(BaseAgent):
    """Agent that ensures the project meets regulatory and compliance requirements."""
    def __init__(self, model):
        super().__init__(
            name="Regulatory",
            model=model,
            system_message=REGULATORY_SYSTEM_PROMPT,
            user_prompt_template=REGULATORY_USER_PROMPT_TEMPLATE,
        )
