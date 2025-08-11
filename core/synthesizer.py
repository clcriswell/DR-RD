from __future__ import annotations

from typing import Dict, List

import openai
from dr_rd.utils.llm_client import llm_call


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
    resp = llm_call(openai, model_id, stage="synth", messages=messages)
    return resp.choices[0].message.content
