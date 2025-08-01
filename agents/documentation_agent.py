from agents.base_agent import BaseAgent

"""Documentation Agent for technical documentation planning."""
class DocumentationAgent(BaseAgent):
    """Agent that outlines the documentation strategy and requirements for the project."""

    def __init__(self):
        super().__init__(
            name="Documentation",
            model="gpt-4",
            system_message="You are a technical writer and documentation expert skilled in creating clear project documentation.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Documentation specialist, your task is {task}. "
                "Provide an outline in Markdown format for project documentation, including user guides, technical manuals, and API references. "
                "Conclude with a JSON structure listing documentation sections and deliverables."
            ),
        )
