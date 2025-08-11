from .base_agent import Agent


class CTOAgent(Agent):
    """Technical strategy and architecture expert."""

    def __init__(self, model_id: str, name: str = "CTO"):
        super().__init__(
            name=name,
            role="CTO",
            model_id=model_id,
            system_prompt="You are a CTO focusing on architecture, scalability, and technical risks.",
        )
