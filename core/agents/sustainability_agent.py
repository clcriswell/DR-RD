from core.agents.base_agent import BaseAgent

"""Sustainability Agent for assessing environmental impact and resource efficiency."""
class SustainabilityAgent(BaseAgent):
    """Agent that evaluates sustainability considerations for the project idea."""
    def __init__(self, model):
        super().__init__(
            name="Sustainability",
            model=model,
            system_message=(
                "You are an environmental sustainability expert focused on eco-friendly design and resource optimization. "
                "You analyze designs for environmental impact, using lifecycle assessments or resource flow diagrams. "
                "Provide justification for each recommendation and be ready to update suggestions if simulations indicate issues (e.g., excessive energy use)."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Sustainability specialist, your task is {task}. "
                "Provide an analysis in Markdown format covering environmental impact, resource usage (with any relevant flow/energy diagrams), and mitigation strategies for negative impacts. "
                "Include reasoning behind each sustainability recommendation (e.g., why a material or process is chosen for its eco-benefits). "
                "Conclude with a JSON summary of sustainability considerations and recommended actions."
            ),
        )
