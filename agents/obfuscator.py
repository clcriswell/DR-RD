"""
Prompt Segmenter & Obfuscator
-----------------------------
Rewrites each domain-specific task so external APIs never see the
user’s full project intent.

Usage:
    from agents.obfuscator import obfuscate_task
    anon = obfuscate_task("Physics", "Determine lift-to-drag ratio for…")
"""

from typing import Dict
import logging
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.llm_client import call_openai

SYSTEM_PROMPT = (
    "You are an R&D anonymizer. Given a research TASK and its DOMAIN, "
    "rewrite the task so it can be sent to an external expert without "
    "revealing the overarching project purpose. Keep the technical essence, "
    "strip proper nouns / final application hints, and limit to ≤2 sentences."
)


def obfuscate_task(domain: str, task: str) -> str:
    """Return an obfuscated version of a single domain task."""
    sel = pick_model(CallHints(stage="exec"))
    logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
    result = call_openai(
        model=sel["model"],
        temperature=0.5,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DOMAIN: {domain}\nTASK: {task}\n\nObfuscated:"},
        ],
        **sel["params"],
    )
    return (result["text"] or "").strip()
