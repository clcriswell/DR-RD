from core.agents.base_agent import BaseAgent

"""Prototyping & Test Lab Manager Agent for rapid prototyping and experimental testing."""


class PrototypingTestLabManagerAgent(BaseAgent):
    """Agent specializing in managing prototypes and lab testing activities."""

    def __init__(self, model):
        super().__init__(
            name="Prototyping & Test Lab Manager",
            model=model,
            system_message=(
                "You are a prototyping and test lab manager skilled in quickly building and "
                "evaluating experimental prototypes. You design efficient testing protocols "
                "(using Design of Experiments techniques) to explore the design space with "
                "minimal iterations. You also manage lab resources and ensure safety and "
                "accuracy in all test procedures."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\\n"
                "As the Prototyping & Test Lab Manager, your task is {task}. "
                "Provide a detailed prototyping and testing plan in Markdown, describing what "
                "prototype versions to build and what variables to test in each iteration. "
                "Outline a series of experiments (leveraging Design of Experiments if applicable) "
                "to cover the project's design space efficiently. Discuss the equipment or setups "
                "needed in the lab and any safety considerations. Include reasoning for how this "
                "plan minimizes time and resource use while maximizing learning. Conclude with a "
                "JSON list of planned prototype tests and their objectives (e.g., 'Test 1: Vary lens "
                "material – Purpose: identify effect on image clarity')."
            ),
        )
