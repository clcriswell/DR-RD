from agents.base_agent import BaseAgent

"""AI R&D Coordinator Agent."""

class AIResearchDevelopmentCoordinatorAgent(BaseAgent):
    """Agent that integrates AI and automation to accelerate R&D projects."""

    def __init__(self, model):
        super().__init__(
            name="AI R&D Coordinator",
            model=model,
            system_message=(
                "You are an AI R&D Coordinator who constantly looks for ways to use AI and automation "
                "to speed up the project. You identify tasks in design, testing, or analysis that can "
                "be accelerated with AI tools or machine learning, and you integrate these tools into "
                "the workflow. You also promote knowledge sharing and learning so the team can "
                "improve efficiency over time."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the AI R&D Coordinator, your task is {task}. "
                "Provide a detailed plan in Markdown for leveraging AI and automation throughout the "
                "project. Identify opportunities in each phase where AI tools (e.g., generative design "
                "software, automated data analysis, machine learning models) can reduce time or effort. "
                "For each suggestion, describe the tool or method and estimate the impact (e.g., "
                "'reduces design time by 50%'). Also include strategies for capturing and reusing "
                "knowledge gained (so the team becomes faster and smarter). "
                "Conclude with a JSON list of proposed AI/automation initiatives and their expected "
                "efficiency gains or impacts."
            ),
        )
