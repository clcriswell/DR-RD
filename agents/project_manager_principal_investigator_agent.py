from agents.base_agent import BaseAgent

"""Project Manager / Principal Investigator Agent for leadership and strategic planning."""


class ProjectManagerPrincipalInvestigatorAgent(BaseAgent):
    """Agent overseeing project vision, timeline, and resource management."""

    def __init__(self, model):
        super().__init__(
            name="Project Manager / Principal Investigator",
            model=model,
            system_message=(
                "You are the project manager and principal investigator, responsible for overall project vision, "
                "timeline, and resource management. You excel at breaking the project into phases with clear milestones, "
                "allocating team resources efficiently, and anticipating risks. You keep the big picture in view while "
                "coordinating all teams towards the end goal."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the Project Manager / Principal Investigator, your task is {task}. "
                "Provide a detailed project roadmap in Markdown, including project phases, milestones, and a timeline. "
                "Outline key deliverables for each phase and the resources (team members, budget, equipment) required. "
                "Include a brief risk management plan identifying potential challenges and mitigation strategies. "
                "Ensure the plan shows how all sub-teams’ efforts integrate over time. "
                "Conclude with a JSON list of major milestones with their expected completion dates or durations."
            ),
        )
