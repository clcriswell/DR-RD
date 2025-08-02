from agents.base_agent import BaseAgent

"""Research Scientist Agent for in-depth analysis and experimentation plans."""
class ResearchScientistAgent(BaseAgent):
    """Agent that conducts research analysis and proposes experiments for the idea."""

    def __init__(self, model):
        super().__init__(
            name="Research Scientist",
            model=model,
            system_message="You are a research scientist with expertise in experimental design and literature review.",
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Research Scientist, your task is {task}. "
                "Provide an in-depth analysis in Markdown format, including relevant background research, potential experiments, and expected results. "
                "Conclude with a JSON summary of proposed experiments and key findings."
            ),
        )
