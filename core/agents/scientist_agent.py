from .base_agent import Agent


class ResearchScientistAgent(Agent):
    """Research specialist for materials, physics and literature."""

    def __init__(self, model_id: str, name: str = "Research"):
        super().__init__(
            name=name,
            role="Research Scientist",
            model_id=model_id,
            system_prompt="You analyze materials, physics and prior literature to guide research.",
        )
