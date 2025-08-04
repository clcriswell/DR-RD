from agents.base_agent import BaseAgent

"""Mechanical & Precision-Motion Engineer Agent for precision motion control tasks."""


class MechanicalPrecisionMotionEngineerAgent(BaseAgent):
    """Agent focused on precision motion control and mechanical staging."""

    def __init__(self, model):
        super().__init__(
            name="Mechanical & Precision-Motion Engineer",
            model=model,
            system_message=(
                "You are a mechanical and precision-motion engineer skilled in designing motion control systems and high-precision stages. "
                "You focus on achieving micron-level accuracy in movement with fast/slow axes, using feedback control and calibration techniques for optimal performance."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Mechanical & Precision-Motion Engineer, your task is {task}. "
                "Provide a detailed plan in Markdown for the precision motion components, including stage designs, actuator selection, and control strategies to achieve high-precision movement. "
                "Discuss fast vs. slow axis design, feedback control loops, and calibration routines for accuracy. "
                "Conclude with a JSON list of key motion components and their design parameters."
            ),
        )
