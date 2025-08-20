from __future__ import annotations

from typing import Dict, List

from core.llm_client import call_openai


def synthesize(idea: str, results_by_role: Dict[str, List[dict]], model_id: str) -> str:
    """Combine agent findings into a unified plan."""
    parts: List[str] = []
    for role, results in results_by_role.items():
        for r in results:
            summary = r.get("findings", [""])[0] if r.get("findings") else ""
            parts.append(f"{role}: {summary}")
    findings = "\n".join(parts)
    messages = [
        {
            "role": "system",
            "content": "You synthesize multi-agent research into a cohesive plan.",
        },
        {
            "role": "user",
            "content": (
                f"Project Idea: {idea}\n\nFindings by role:\n{findings}\n\n"
                "Produce a unified plan referencing each role's contribution."
            ),
        },
    ]
    result = call_openai(model=model_id, messages=messages)
    return result["text"] or ""
