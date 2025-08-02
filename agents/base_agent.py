class BaseAgent:
    """Base class for role-specific agents."""

    def __init__(self, name: str, model: str, system_message: str, user_prompt_template: str):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.user_prompt_template = user_prompt_template

    def run(self, idea: str, task: str, design_depth: str = "Medium") -> str:
        """Construct the prompt and call the OpenAI API. Returns assistant text."""
        import openai

        # Base prompt from template
        prompt = self.user_prompt_template.format(idea=idea, task=task)

        # Adjust prompt detail based on design_depth
        design_depth = design_depth.capitalize()  # normalize casing (Low/Medium/High)
        if design_depth == "High":
            prompt += (
                "\n\n**Design Depth: High** – Include all relevant component-level details. "
                "Provide exhaustive technical depth, with complete diagrams, schematics, and trade-off analyses for design decisions."
            )
        elif design_depth == "Low":
            prompt += (
                "\n\n**Design Depth: Low** – Provide a brief high-level overview with minimal technical detail. "
                "Focus on core concepts and avoid deep specifics or extensive diagrams."
            )
        else:  # Medium or default
            prompt += (
                "\n\n**Design Depth: Medium** – Provide a balanced level of detail. "
                "Include key diagrams or specifications and reasoning for major decisions without delving into excessive minutiae."
            )

        # Call OpenAI ChatCompletion with system and user messages
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
