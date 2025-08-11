from .base_agent import Agent


class RegulatoryAgent(Agent):
    """Compliance and regulatory advisor."""

    def __init__(self, model_id: str, name: str = "Regulatory"):
        super().__init__(
            name=name,
            role="Regulatory Specialist",
            model_id=model_id,
            system_prompt="You ensure compliance with standards such as FDA, ISO and FCC.",
        )
