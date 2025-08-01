from agents.base_agent import BaseAgent

"""Patent Agent for intellectual property and patentability analysis."""
class PatentAgent(BaseAgent):
    """Agent that evaluates patentability and IP strategy for the project idea."""

    def __init__(self):
        super().__init__(
            name="Patent",
            model="gpt-4",
            system_message="You are a patent attorney and innovation expert focusing on intellectual property.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Patent expert, your task is {task}. "
                "Provide an analysis in Markdown format of patentability, existing patents to consider, and IP strategy. "
                "Conclude with a JSON list of potential patent ideas or relevant patent references."
            ),
        )
