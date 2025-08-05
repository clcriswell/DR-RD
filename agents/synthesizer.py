"""
Prototype Synthesizer / Final Composer
--------------------------------------
Combines the user's original idea with the (optionally loop-refined)
multi-domain answers to draft a cohesive, testable design or development
plan.  Returns Markdown text ready for Streamlit rendering.

Call:
    from agents.synthesizer import synthesize
    markdown = synthesize(user_idea, answers_dict)
"""
from typing import Dict
import openai
from config.agent_models import AGENT_MODEL_MAP

_TEMPLATE = """\
You are a multi-disciplinary R&D lead.

**Goal**: “{idea}”

We have gathered the following domain findings (some may include loop-refined
addenda separated by "--- *(Loop-refined)* ---"):

{findings_md}

Write a cohesive technical proposal that:

1. Summarizes key insights per domain (concise bullet list each).
2. Integrates those insights into a unified prototype / development plan.
3. Calls out any remaining unknowns or recommended next experiments.
4. Uses clear Markdown with headings:
   - ## Executive Summary
   - ## Domain Insights
   - ## Integrated Prototype Plan
   - ## Remaining Unknowns
"""

def synthesize(idea: str, answers: Dict[str, str]) -> str:
    findings_md = "\n".join(
        f"### {d}\n{answers[d]}" for d in answers
    )
    prompt = _TEMPLATE.format(idea=idea, findings_md=findings_md)

    resp = openai.chat.completions.create(
        model=AGENT_MODEL_MAP["Synthesizer"],
        temperature=0.3,
        messages=[
            {"role": "system", "content": "You are an expert R&D writer."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


def compose_final_proposal(idea: str, answers: Dict[str, str], include_simulations: bool = False) -> str:
    """Compose a Prototype Build Guide integrating agent contributions."""
    model = AGENT_MODEL_MAP["Synthesizer"]
    contributions = "\n".join(f"### {role}\n{content}" for role, content in answers.items())
    sections = [
        "1. Executive Summary",
        "2. Bill of Materials (as a table)",
        "3. Step-by-Step Instructions (numbered, with reasoning)",
    ]
    if include_simulations:
        sections.append("4. Simulation & Test Results (if available)")
    prompt = (
        "You are a senior R&D expert. Produce a Prototype Build Guide in Markdown with these sections:\n"
        + "\n".join(sections)
        + "\nIntegrate these agent contributions into one cohesive document.\n\n"
        + f"Project Idea: {idea}\n\n"
        + f"Agent Contributions:\n{contributions}"
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    final_document = response.choices[0].message.content
    return final_document


class SynthesizerAgent:
    """Lightweight agent wrapper for composing final proposals."""

    def __init__(self, model: str):
        self.model = model

    def run(self, idea: str, answers: Dict[str, str], include_simulations: bool = False) -> str:
        """Delegate to compose_final_proposal using the configured model."""
        return compose_final_proposal(idea, answers, include_simulations=include_simulations)
