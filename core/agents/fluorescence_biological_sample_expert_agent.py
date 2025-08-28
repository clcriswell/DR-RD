from core.agents.base_agent import BaseAgent

"""Fluorescence & Biological Sample Expert Agent for sample prep and imaging guidance."""


class FluorescenceBiologicalSampleExpertAgent(BaseAgent):
    """Agent specializing in fluorescence imaging and biological sample preparation."""

    def __init__(self, model):
        super().__init__(
            name="Fluorescence / Biological Sample Expert",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/fluorescence_biological_sample_expert_agent.json
                "You are a fluorescence and biological sample expert with experience in biochemistry and microscopy. "
                "You know how to prepare and handle fluorescent samples, select appropriate fluorophores or biomarkers, and optimize imaging protocols. "
                "You consider factors like excitation/emission spectra, photobleaching, and biosafety in experimental design."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/fluorescence_biological_sample_expert_agent.json
                "Project Idea: {idea}\nAs the Fluorescence / Biological Sample Expert, your task is {task}. "
                "Provide a detailed plan in Markdown for the biological and fluorescence aspects of the project. "
                "Recommend fluorescent markers or assays to use, including their excitation/emission wavelengths and why they suit the project goals. "
                "Describe how to prepare samples or automate sample handling (e.g., using a pipetting robot or specific protocols), and any safety or contamination precautions. "
                "Include reasoning for each choice (e.g., why a certain fluorophore is ideal). "
                "Conclude with a JSON list of selected fluorophores/biological assays and their key properties or usage notes."
            ),
        )
