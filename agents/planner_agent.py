from agents.base_agent import BaseAgent
import logging

"""Planner Agent for developing project plans."""
class PlannerAgent(BaseAgent):
    """Agent that creates a detailed project plan for the given idea."""

    def __init__(self, model):
        super().__init__(
            name="Planner",
            model=model,
            system_message=(
                "You are an expert project planner specializing in turning ideas into actionable plans."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the Planner, your task is {task}.\n\n"
                "Return **only** a JSON object mapping each relevant team role (from the list below) to one or two succinct tasks. "
                "Include a role only if it would reasonably contribute to this project:\n"
                "  - Mechanical Systems Lead\n"
                "  - Materials & Process Engineer\n"
                "  - Chemical & Surface Science Specialist\n"
                "  - Quantum Optics Physicist\n"
                "  - Nonlinear Optics / Crystal Engineer\n"
                "  - Optical Systems Engineer\n"
                "  - Mechanical & Precision-Motion Engineer\n"
                "  - Photonics Electronics Engineer\n"
                "  - Electronics & Embedded Controls Engineer\n"
                "  - Software / Image-Processing Specialist\n"
                "  - Fluorescence / Biological Sample Expert\n"
                "  - Systems Integration & Validation Engineer\n"
                "  - Data Scientist / Analytics Engineer\n"
                "  - Regulatory & Compliance Lead\n"
                "  - Prototyping & Test Lab Manager\n"
                "  - Project Manager / Principal Investigator\n"
                "  - Product Manager / Translational Lead\n"
                "  - AI R&D Coordinator\n\n"
                "Only include roles that are relevant, and do not include any roles outside this list. "
                "Use each role name exactly as given above as JSON keys, and provide a brief task description for each selected role."
            ),
        )

    def run(self, idea: str, task: str) -> dict:
        """Return the planner's JSON summary as a Python dict."""
        import openai, json

        prompt = self.user_prompt_template.format(idea=idea, task=task)

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        }

        # Only newer models (e.g. gpt-4o, gpt-4.1) support the
        # `response_format` parameter for structured JSON output. Older
        # completion models will raise a 400 error if it is supplied. To keep
        # compatibility with both we add the parameter conditionally.
        if self.model.startswith(("gpt-4o", "gpt-4.1")):
            kwargs["response_format"] = {"type": "json_object"}

        response = openai.chat.completions.create(**kwargs)
        raw_text = response.choices[0].message.content
        logging.debug("Planner raw response: %s", raw_text)
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Planner returned invalid JSON: {raw_text}") from e
