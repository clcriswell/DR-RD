from core.agents.base_agent import BaseAgent

"""Documentation Agent for technical documentation planning."""
class DocumentationAgent(BaseAgent):
    """Agent that outlines the documentation strategy and requirements for the project."""
    def __init__(self, model):
        super().__init__(
            name="Documentation",
            model=model,
            # Emphasize inclusion of diagrams and clarity
            system_message=(
                # Schema: dr_rd/schemas/documentation_agent.json
                "You are a technical writer and documentation expert skilled in creating clear, comprehensive project documentation. "
                "You include diagrams or schematics where helpful and justify documentation structure decisions. "
                "You are prepared to update documentation plans based on simulation feedback or design changes."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/documentation_agent.json
                "Project Idea: {idea}\nAs the Documentation specialist, your task is {task}. "
                "Provide an outline in Markdown format for project documentation, including user guides, technical manuals, API references, and appropriate diagrams/illustrations for clarity. "
                "Include reasoning for the chosen documentation structure and highlight any critical sections. "
                "Conclude with a JSON structure listing documentation sections and deliverables."
            ),
        )
