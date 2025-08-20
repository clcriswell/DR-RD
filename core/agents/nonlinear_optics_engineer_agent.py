from core.agents.base_agent import BaseAgent

"""Nonlinear Optics Engineer Agent focusing on frequency conversion materials and design."""


class NonlinearOpticsEngineerAgent(BaseAgent):
    """Agent that designs and selects nonlinear optical components."""

    def __init__(self, model):
        super().__init__(
            name="Nonlinear Optics Engineer",
            model=model,
            system_message=(
                "You are a nonlinear optics engineer with deep knowledge of optical materials and frequency conversion techniques. "
                "You design and select nonlinear crystals (e.g., for second-harmonic generation or SPDC), optimizing parameters like phase-matching, poling period, and crystal orientation. "
                "You also consider fabrication or sourcing of specialized optical materials."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Nonlinear Optics Engineer, your task is {task}. "
                "Provide a detailed plan in Markdown for the nonlinear optical components, including selection or engineering of crystals for frequency conversion (e.g., second-harmonic generation, parametric conversion). "
                "Propose specific crystal materials and configurations (such as poling periods, phase-matching angles) and how they would be obtained or fabricated. "
                "Discuss trade-offs between different nonlinear materials. "
                "Conclude with a JSON list of chosen nonlinear optical materials/crystals and their key design parameters."
            ),
        )
