"""
Loop Orchestrator
-----------------
Reviews the first-round answers, decides where depth is lacking,
and (optionally) issues ONE follow-up query per domain to enrich
the answer.  Uses OpenAI for the review, then re-uses the existing
obfuscator + router for follow-up.

Call:
    from agents.orchestrator import refine_once
    enriched = refine_once(plan, answers)
"""

from typing import Dict
import openai
from agents.obfuscator import obfuscate_task
from agents.router import route


def _needs_follow_up(domain: str, task: str, answer: str) -> str | None:
    """Return a follow-up question *or* None if answer is judged complete."""
    review = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior R&D reviewer. If the answer below is "
                    "technically thorough and actionable, reply exactly "
                    "'COMPLETE'. If not, write ONE specific follow-up question "
                    "that would close the biggest gap. No other text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"DOMAIN: {domain}\n"
                    f"Original task: {task}\n"
                    f"Answer so far: {answer}"
                ),
            },
        ],
    )
    proposal = review.choices[0].message.content.strip()
    return None if proposal.upper().startswith("COMPLETE") else proposal


def refine_once(plan: Dict[str, str], answers: Dict[str, str]) -> Dict[str, str]:
    """Return answers, optionally enriched with one follow-up per domain."""
    updated = answers.copy()
    for domain in plan:
        follow_up = _needs_follow_up(domain, plan[domain], updated[domain])
        if not follow_up:
            continue

        # Obfuscate & re-query
        obf = obfuscate_task(domain, follow_up)
        extra = route(obf)

        updated[domain] += "\n\n--- *(Loop-refined)* ---\n" + extra
    return updated
