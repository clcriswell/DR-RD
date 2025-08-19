from agents.base_agent import BaseAgent, LLMRoleAgent

"""CTO Agent for technical strategy and overview."""
class CTOAgent(BaseAgent):
    """Agent that provides technical direction and architecture for the project idea."""
    def __init__(self, model):
        super().__init__(
            name="CTO",
            model=model,
            # Expanded system message to emphasize diagrams, justification, and simulation feedback readiness
            system_message=(
                "You are a Chief Technology Officer with deep technical expertise and strategic vision. "
                "You excel at creating high-level system architectures (including block diagrams) and outlining technical strategies. "
                "Provide clear justifications for each major technical choice, and be prepared to revise your plans based on simulation feedback."
            ),
            # Expanded prompt template to request diagrams, specs, test plans, and reasoning
            user_prompt_template=(
                "Project Idea: {idea}\nAs the CTO, your task is {task}. "
                "Provide a thorough technical assessment and strategy in Markdown format, including high-level architecture diagrams, key components/material specifications, tools, and resource estimations. "
                "Include reasoning and justification for each major technical decision, and outline any preliminary test plans to validate feasibility. "
                "Conclude with a JSON list of key technical decisions and resource requirements."
            ),
        )


class SimpleCTOAgent(LLMRoleAgent):
    def __init__(self, model: str):
        super().__init__("CTO", model)
