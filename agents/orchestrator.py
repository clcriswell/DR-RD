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
from agents.obfuscator import obfuscate_task
from agents.router import route
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.llm_client import call_openai


def _needs_follow_up(domain: str, task: str, answer: str) -> str | None:
    """Return a follow-up question *or* None if answer is judged complete."""
    sel = pick_model(CallHints(stage="exec"))
    result = call_openai(
        model=sel["model"],
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
        **sel["params"],
    )
    proposal = (result["text"] or "").strip()
    return None if proposal.upper().startswith("COMPLETE") else proposal


def refine_once(plan: Dict[str, str], answers: Dict[str, str]) -> Dict[str, str]:
    """Return answers, optionally enriched with one follow-up per domain."""
    updated = answers.copy()
    for domain, task in plan.items():
        current_answer = updated.get(domain)
        if current_answer is None:
            # Skip refinement if no answer was provided for this domain
            continue

        follow_up = _needs_follow_up(domain, task, current_answer)
        if not follow_up:
            continue

        # Obfuscate & re-query
        obf = obfuscate_task(domain, follow_up)
        extra = route(obf)

        updated[domain] += "\n\n--- *(Loop-refined)* ---\n" + extra
    return updated
