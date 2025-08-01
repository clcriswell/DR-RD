from agents.base_agent import BaseAgent

"""QA Agent for quality assurance and testing strategy."""
class QAAgent(BaseAgent):
    """Agent that outlines testing strategies and quality assurance plans for the project."""

    def __init__(self):
        super().__init__(
            name="QA",
            model="gpt-4",
            system_message="You are a quality assurance expert focused on testing, validation, and reliability.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the QA specialist, your task is {task}. "
                "Provide a comprehensive testing and QA strategy in Markdown format, including test plans, quality metrics, and risk mitigation. "
                "Conclude with a JSON summary of test cases and quality criteria."
            ),
        )
