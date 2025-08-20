from core.agents.base_agent import BaseAgent

class FinanceAgent(BaseAgent):
    """Financial analyst for budgeting and cost estimates."""

    def __init__(self, model: str):
        super().__init__(
            name="Finance",
            model=model,
            system_message="You evaluate budgets, BOM costs and financial risks.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Finance lead, your task is {task}."
            ),
        )
