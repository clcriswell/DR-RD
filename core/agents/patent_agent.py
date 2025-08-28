from core.agents.base_agent import BaseAgent
from prompts.prompts import (
    PATENT_SYSTEM_PROMPT,
    PATENT_USER_PROMPT_TEMPLATE,
)

"""Patent Agent for intellectual property and patentability analysis."""
class PatentAgent(BaseAgent):
    """Agent that evaluates patentability and IP strategy for the project idea."""
    def __init__(self, model):
        super().__init__(
            name="Patent",
            model=model,
            system_message=PATENT_SYSTEM_PROMPT,
            user_prompt_template=PATENT_USER_PROMPT_TEMPLATE,
                # Schema: dr_rd/schemas/patent_agent.json
        )
