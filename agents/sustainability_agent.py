from agents.base_agent import BaseAgent

"""Sustainability Agent for assessing environmental impact and resource efficiency."""

class SustainabilityAgent(BaseAgent):
    """Agent that evaluates sustainability considerations for the project idea."""

    def __init__(self, model):
        super().__init__(
            name="Sustainability",
            model=model,
            system_message=(
                "You are an environmental sustainability expert focused on eco-friendly design and resource optimization."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Sustainability specialist, your task is {task}. "
                "Provide an analysis in Markdown format covering environmental impact, resource usage, and mitigation strategies. "
                "Conclude with a JSON summary of sustainability considerations and recommended actions."
            ),
        )
