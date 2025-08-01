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
        model="gpt-4o-mini",         # upgrade to gpt-4o if you like
        temperature=0.3,
        messages=[
            {"role": "system", "content": "You are an expert R&D writer."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


def compose_final_proposal(idea: str, answers: Dict[str, str]) -> str:
    """Compose a final Markdown proposal integrating all agent responses."""
    model = "gpt-4"
    prompt = (
        f"We have an R&D project idea: {idea}\n\n"
        "Below are contributions from various team members (Planner, CTO, Research Scientist, Engineer, QA, Regulatory, Patent, Documentation) addressing different aspects of the project.\n"
        "Please synthesize these contributions into one cohesive proposal. The proposal should start with a **Summary** section (covering the main points of the idea), followed by a **Table of Contents**, and then a detailed section for each aspect contributed by the team. Ensure the final document is well-structured and written in a single voice.\n\n"
        "Contributions:\n"
    )
    for role, content in answers.items():
        prompt += f"{role} Contribution:\n{content}\n\n"
    prompt += (
        "End of contributions.\n"
        "Now draft the complete R&D proposal in Markdown as described, with clear section headings (Summary, Table of Contents, and one section per role)."
    )

    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    final_document = response.choices[0].message.content
    return final_document
