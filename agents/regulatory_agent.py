from agents.base_agent import BaseAgent

"""Regulatory Agent for compliance and standards analysis."""
class RegulatoryAgent(BaseAgent):
    """Agent that ensures the project meets regulatory and compliance requirements."""

    def __init__(self, model):
        super().__init__(
            name="Regulatory",
            model=model,
            system_message="You are a regulatory compliance expert with knowledge of industry standards and laws.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Regulatory expert, your task is {task}. "
                "Provide a thorough analysis of regulatory requirements and compliance steps in Markdown format, including any certifications or standards needed. "
                "Conclude with a JSON checklist of regulatory steps and compliance requirements."
            ),
        )
