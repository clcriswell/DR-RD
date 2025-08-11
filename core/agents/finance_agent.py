from .base_agent import Agent


class FinanceAgent(Agent):
    """Financial analyst for budgeting and cost estimates."""

    def __init__(self, model_id: str, name: str = "Finance"):
        super().__init__(
            name=name,
            role="Finance Analyst",
            model_id=model_id,
            system_prompt="You evaluate budgets, BOM costs and financial risks.",
        )
