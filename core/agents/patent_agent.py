from core.agents.base_agent import BaseAgent

"""Patent Agent for intellectual property and patentability analysis."""
class PatentAgent(BaseAgent):
    """Agent that evaluates patentability and IP strategy for the project idea."""
    def __init__(self, model):
        super().__init__(
            name="Patent",
            model=model,
            system_message=(
                "You are a patent attorney and innovation expert focusing on intellectual property. "
                "You thoroughly analyze existing patents and technical disclosures, referencing diagrams or figures if relevant. "
                "You justify your conclusions on patentability and can adjust IP strategy if new technical feedback (e.g., simulation data) warrants it."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Patent expert, your task is {task}. "
                "Provide an analysis in Markdown format of patentability, including any existing patents (with relevant patent figures or diagrams if applicable) and an IP strategy. "
                "Include reasoning behind each recommendation (e.g., why certain features are patentable or not). "
                "Conclude with a JSON list of potential patent ideas or relevant patent references."
            ),
        )
