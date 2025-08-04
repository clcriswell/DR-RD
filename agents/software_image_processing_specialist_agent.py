from agents.base_agent import BaseAgent

"""Software & Image-Processing Specialist Agent for algorithm and pipeline design."""


class SoftwareImageProcessingSpecialistAgent(BaseAgent):
    """Agent focusing on software algorithms and image-processing pipeline development."""

    def __init__(self, model):
        super().__init__(
            name="Software / Image-Processing Specialist",
            model=model,
            system_message=(
                "You are a software and image-processing specialist who develops algorithms for data analysis and system control. "
                "You design image-processing pipelines (for noise reduction, feature extraction, etc.) and software architectures to manage data flow. "
                "You also consider user interface or control software for the system, ensuring the software is efficient and reliable."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Software / Image-Processing Specialist, your task is {task}. "
                "Provide a detailed plan in Markdown for the software components and image-processing pipeline. "
                "Describe the algorithms or models (e.g., a neural network for image denoising or analysis) and the software architecture (how data is collected, processed, and stored). "
                "Mention any specific libraries or frameworks that would be used, and how the software will interface with hardware or the user. "
                "Conclude with a JSON list of key software modules/algorithms and their primary functions."
            ),
        )
