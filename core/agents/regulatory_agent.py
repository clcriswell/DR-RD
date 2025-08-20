from core.agents.base_agent import BaseAgent

"""Regulatory Agent for compliance and standards analysis."""
class RegulatoryAgent(BaseAgent):
    """Agent that ensures the project meets regulatory and compliance requirements."""
    def __init__(self, model):
        super().__init__(
            name="Regulatory",
            model=model,
            system_message=(
                "You are a regulatory compliance expert with knowledge of industry standards and laws. "
                "You provide detailed compliance analysis, referencing standards and guidelines. "
                "You justify how the design meets (or needs modifications to meet) each requirement and adjust recommendations if testing/simulation reveals new issues."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Regulatory expert, your task is {task}. "
                "Provide a thorough analysis of regulatory requirements and compliance steps in Markdown format, including any certifications or standards needed, and mapping of system components to regulations. "
                "Include justification for each compliance recommendation (e.g., why a certain standard applies). "
                "Conclude with a JSON checklist of regulatory steps and compliance requirements."
            ),
        )
