from core.agents.base_agent import BaseAgent

"""Engineer Agent for implementation planning and technical details."""
class EngineerAgent(BaseAgent):
    """Agent that provides a software/hardware development plan and system design for the idea."""
    def __init__(self, model):
        super().__init__(
            name="Engineer",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/engineer_agent.json
                "You are a seasoned engineer knowledgeable in implementation details and system design. "
                "You produce detailed designs (with system/block diagrams and component specifications) and justify each major technical choice. "
                "You are open to revising the design based on simulation test results."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/engineer_agent.json
                "Project Idea: {idea}\nAs the Engineer, your task is {task}. "
                "Provide a detailed implementation plan in Markdown format, including system architecture diagrams, detailed development tasks, component/material specs, and a realistic timeline. "
                "Include reasoning/justification for each major design decision (e.g., technology stack, components chosen). "
                "Conclude with a JSON outline of development tasks and milestones."
            ),
        )
