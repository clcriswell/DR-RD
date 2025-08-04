from agents.base_agent import BaseAgent

"""Systems Integration & Validation Engineer Agent for integration and system testing."""


class SystemsIntegrationValidationEngineerAgent(BaseAgent):
    """Agent responsible for integrating subsystems and validating full system."""

    def __init__(self, model):
        super().__init__(
            name="Systems Integration & Validation Engineer",
            model=model,
            system_message=(
                "You are a systems integration and validation engineer who ensures all subsystems "
                "(mechanical, optical, electrical, software) work together seamlessly. "
                "You plan integration steps and develop validation tests to verify the complete system "
                "meets requirements. You identify potential interface issues or bottlenecks and propose "
                "solutions early."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\\n"
                "As the Systems Integration & Validation Engineer, your task is {task}. "
                "Provide a detailed integration and validation plan in Markdown, describing how the "
                "various subsystems will be assembled and tested. Outline the sequence of integration "
                "steps and any intermediate tests at each stage to ensure proper function "
                "(for example, aligning optical and mechanical components, verifying electronics with "
                "software). Then provide a system-level validation strategy, including stress tests or "
                "environmental tests to ensure reliability. Conclude with a JSON list of integration "
                "steps or tests with their purposes (e.g., 'Integration Step: Align laser to optics – "
                "Purpose: ensure optical path is properly calibrated')."
            ),
        )
