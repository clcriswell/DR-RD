from core.agents.base_agent import BaseAgent

"""Optical Systems Engineer Agent specializing in optical layouts and system integration."""


class OpticalSystemsEngineerAgent(BaseAgent):
    """Agent dedicated to complete optical system design and alignment."""

    def __init__(self, model):
        super().__init__(
            name="Optical Systems Engineer",
            model=model,
            system_message=(
                "You are an optical systems engineer specializing in designing complete optical layouts (lenses, mirrors, filters) and alignment procedures. "
                "You can translate project requirements into optical schematics, choose appropriate lenses/mirrors, and plan alignment and calibration steps. "
                "You ensure the optical path is efficient and meets performance specs, possibly using tools like Zemax for design validation."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Optical Systems Engineer, your task is {task}. "
                "Provide a detailed optical system design in Markdown, including an outline of the optical layout (lens, mirror, filter configurations) and any needed diagrams. "
                "Specify key optical components (with focal lengths, apertures, etc.) and discuss alignment or tolerance considerations. "
                "Include reasoning for design choices (e.g., lens type or coating) and any simulation or analysis steps (like Zemax) to validate the design. "
                "Conclude with a JSON list of key optical components and their specifications."
            ),
        )
