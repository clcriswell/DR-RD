from agents.base_agent import BaseAgent

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
                "Return **only** a JSON object mapping each of these roles exactly:\n"
                "  - CTO\n"
                "  - Research Scientist\n"
                "  - Engineer\n"
                "  - QA Specialist\n"
                "  - Regulatory Specialist\n"
                "  - Patent Specialist\n"
                "  - Documentation Specialist\n"
                "  - Sustainability Specialist\n\n"
                "to one or two succinct research or implementation tasks each.\n"
                "Do not include any other keys."
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
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            raise ValueError("Planner returned invalid JSON") from e
