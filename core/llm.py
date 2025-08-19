import os
from openai import OpenAI


def make_chat(model: str, system_prompt: str, user_prompt: str) -> str:
    """Send a single-turn chat completion request and return the content."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content
