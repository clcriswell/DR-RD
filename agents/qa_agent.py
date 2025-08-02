from agents.base_agent import BaseAgent

"""QA Agent for quality assurance and testing strategy."""
class QAAgent(BaseAgent):
    """Agent that outlines testing strategies and quality assurance plans for the project."""
    def __init__(self, model):
        super().__init__(
            name="QA",
            model=model,
            system_message=(
                "You are a quality assurance expert focused on testing, validation, and reliability. "
                "You create comprehensive test plans (including test cases, environments, and success criteria) and provide justification for each testing approach. "
                "You will revise testing plans based on simulation outcomes or observed issues."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the QA specialist, your task is {task}. "
                "Provide a comprehensive testing and QA strategy in Markdown format, including detailed test plans (covering functional, performance, and stress tests), quality metrics, and risk mitigation strategies. "
                "Include reasoning for how each test addresses project risks or requirements. "
                "Conclude with a JSON summary of test cases and quality criteria."
            ),
        )
