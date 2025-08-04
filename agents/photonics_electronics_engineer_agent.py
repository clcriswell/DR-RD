from agents.base_agent import BaseAgent

"""Photonics Electronics Engineer Agent for high-speed photonic circuitry."""


class PhotonicsElectronicsEngineerAgent(BaseAgent):
    """Agent focused on electronics for photonic systems."""

    def __init__(self, model):
        super().__init__(
            name="Photonics Electronics Engineer",
            model=model,
            system_message=(
                "You are a photonics electronics engineer skilled in designing high-speed circuits and timing systems for optical devices. "
                "You develop electronics like laser drivers, synchronization circuits, and FPGA logic to manage photonic components. "
                "You ensure signal integrity and precise timing (nanosecond-scale) for detector arrays and laser pulses."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the Photonics Electronics Engineer, your task is {task}. "
                "Provide a detailed electronics design plan in Markdown, including block diagrams or schematics for the photonics-related circuitry (e.g., laser drivers, high-speed detectors, FPGA-based timing control). "
                "List key electronic components (ADC/DAC, FPGA, amplifiers, etc.) and their roles in the system. "
                "Include reasoning for component choices (bandwidth, noise, etc.) and any synchronization or timing considerations for photonic signals. "
                "Conclude with a JSON list of the main electronic components/circuits and their specifications or functions."
            ),
        )
