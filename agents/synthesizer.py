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


def compose_final_proposal(idea: str, answers: Dict[str, str], include_simulations: bool = False) -> str:
    """Compose a final Markdown proposal integrating all agent responses (and simulation results if requested)."""
    model = "gpt-4"
    # Begin prompt with project idea and context
    prompt = (
        f"We have an R&D project idea: {idea}\n\n"
        "Below are contributions from various team members (Planner, CTO, Research Scientist, Engineer, QA, Regulatory, Patent, Documentation), each addressing different aspects of the project.\n"
        "Please synthesize these contributions into one cohesive proposal. The proposal should start with a **Summary** section (covering the main points of the idea), followed by a **Table of Contents**, and then a detailed section for each aspect contributed by the team. Ensure the final document is well-structured and written in a single voice.\n\n"
        "Contributions:\n"
    )
    # Append each role's contribution (which may include simulation results if present)
    for role, content in answers.items():
        prompt += f"{role} Contribution:\n{content}\n\n"
    prompt += "End of contributions.\n"
    # Add instruction for Simulation Results section if needed
    if include_simulations:
        prompt += (
            "Now draft the complete R&D proposal in Markdown as described, with clear section headings "
            "(Summary, Table of Contents, one section per role, **Simulation Results**). "
            "Include a dedicated **Simulation Results** section at the end that compiles and summarizes all the performance metrics from the simulations above, rather than listing them in each role’s section."
        )
    else:
        prompt += (
            "Now draft the complete R&D proposal in Markdown as described, with clear section headings "
            "(Summary, Table of Contents, and one section per role)."
        )
    # Call the OpenAI API to generate the proposal
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    final_document = response.choices[0].message.content
    return final_document
