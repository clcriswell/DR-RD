from agents.base_agent import BaseAgent

"""Planner Agent for developing project plans."""
class PlannerAgent(BaseAgent):
    """Agent that creates a detailed project plan for the given idea."""

    def __init__(self):
        super().__init__(
            name="Planner",
            model="gpt-4",
            system_message=(
                "You are an expert project planner specializing in turning ideas into actionable plans."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Planner, your task is {task}. "
                "Provide a detailed project plan in Markdown format, including milestones and timelines. "
                "Conclude with a JSON summary of the key planning steps and deadlines."
            ),
        )
