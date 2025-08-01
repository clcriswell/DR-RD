from agents.base_agent import BaseAgent

"""CTO Agent for technical strategy and overview."""
class CTOAgent(BaseAgent):
    """Agent that provides technical direction and architecture for the project idea."""

    def __init__(self):
        super().__init__(
            name="CTO",
            model="gpt-4",
            system_message="You are a Chief Technology Officer with deep technical expertise and strategic vision.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the CTO, your task is {task}. "
                "Provide a thorough technical assessment and strategy in Markdown format, including architecture, tools, and resource estimations. "
                "Conclude with a JSON list of key technical decisions and resource requirements."
            ),
        )
