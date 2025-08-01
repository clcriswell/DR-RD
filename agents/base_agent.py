class BaseAgent:
    """Base class for role-specific agents."""

    def __init__(self, name: str, model: str, system_message: str, user_prompt_template: str):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.user_prompt_template = user_prompt_template

    def run(self, idea: str, task: str) -> str:
        """Construct the prompt and call the OpenAI API. Returns assistant text."""
        import openai

        prompt = self.user_prompt_template.format(idea=idea, task=task)
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
