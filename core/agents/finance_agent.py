from core.agents.base_agent import BaseAgent
from prompts.prompts import (
    FINANCE_SYSTEM_PROMPT,
    FINANCE_USER_PROMPT_TEMPLATE,
)

class FinanceAgent(BaseAgent):
    """Financial analyst for budgeting and cost estimates."""

    def __init__(self, model: str):
        super().__init__(
            name="Finance",
            model=model,
            system_message=FINANCE_SYSTEM_PROMPT,
            user_prompt_template=FINANCE_USER_PROMPT_TEMPLATE,
                # Schema: dr_rd/schemas/finance_agent.json
        )
