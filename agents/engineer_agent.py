from agents.base_agent import BaseAgent

"""Engineer Agent for implementation planning and technical details."""
class EngineerAgent(BaseAgent):
    """Agent that provides a software development plan and system design for the idea."""

    def __init__(self, model):
        super().__init__(
            name="Engineer",
            model=model,
            system_message="You are a seasoned software engineer knowledgeable in implementation details and system design.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Engineer, your task is {task}. "
                "Provide a detailed implementation plan in Markdown format, including system architecture, development tasks, and timeline. "
                "Conclude with a JSON outline of development tasks and milestones."
            ),
        )
