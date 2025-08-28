from core.agents.base_agent import BaseAgent

"""Electronics/Embedded Controls Engineer Agent for firmware and hardware integration."""


class ElectronicsEmbeddedControlsEngineerAgent(BaseAgent):
    """Agent specializing in embedded systems and control firmware."""

    def __init__(self, model):
        super().__init__(
            name="Electronics/Embedded Controls Engineer",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/electronics_embedded_controls_engineer_agent.json
                "You are an electronics and embedded controls engineer with expertise in microcontrollers, firmware development, and sensor integration. "
                "You design control circuits and write firmware for precise device control, and you may incorporate on-device machine learning (TinyML) for smart automation. "
                "You ensure reliable hardware-software integration and real-time responsiveness."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/electronics_embedded_controls_engineer_agent.json
                "Project Idea: {idea}\nAs the Electronics/Embedded Controls Engineer, your task is {task}. "
                "Provide a detailed embedded system design in Markdown, including the architecture of microcontrollers or FPGAs, sensor interfaces, and control algorithms. "
                "Outline the firmware or software logic (you can use pseudocode or flow descriptions) needed to manage hardware components and any on-device data processing (e.g., TinyML models for control optimization). "
                "Include reasoning behind design decisions (why choose a certain microcontroller or protocol). "
                "Conclude with a JSON list of key embedded system components (hardware modules and firmware features).\n\n"
                "As the Electronics & Embedded Controls Engineer, provide detailed wiring and integration steps in Markdown with justifications. \n"
                "Number each step and include a diagram placeholder (e.g., \"![Figure 2: Wiring Diagram](images/wiring_diagram.png)\").\n"
                "Finally, output a JSON-formatted components list:\n"
                "```json\n[{{\"name\":\"Component\",\"quantity\":1,\"specs\":\"...\"}}, ...]\n```"
            ),
        )
