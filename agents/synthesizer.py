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
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.utils.llm_client import llm_call, log_usage
import logging
import base64

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

    sel = pick_model(CallHints(stage="synth"))
    logging.info(f"Model[synth]={sel['model']} params={sel['params']}")
    resp = llm_call(
        openai,
        sel["model"],
        stage="synth",
        messages=[
            {"role": "system", "content": "You are an expert R&D writer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        **sel["params"],
    )
    usage = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", None)
    if usage:
        log_usage(
            stage="synth",
            model=sel["model"],
            pt=getattr(usage, "prompt_tokens", 0),
            ct=getattr(usage, "completion_tokens", 0),
        )
    return resp.choices[0].message.content.strip()


def compose_final_proposal(idea: str, answers: Dict[str, str], include_simulations: bool = False) -> str:
    """Compose a Prototype Build Guide integrating agent contributions."""
    sel = pick_model(CallHints(stage="synth", final_pass=True))
    logging.info(f"Model[synth]={sel['model']} params={sel['params']}")
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
    response = llm_call(
        openai,
        sel["model"],
        stage="synth",
        messages=[{"role": "user", "content": prompt}],
        **sel["params"],
    )
    usage = response.choices[0].usage if hasattr(response.choices[0], "usage") else getattr(response, "usage", None)
    if usage:
        log_usage(
            stage="synth",
            model=sel["model"],
            pt=getattr(usage, "prompt_tokens", 0),
            ct=getattr(usage, "completion_tokens", 0),
        )
    final_document = response.choices[0].message.content

    # Optional: generate 1-2 schematic images
    try:
        import openai as _openai
        prompts = [
            f"Schematic diagram of the proposed prototype based on: {idea}",
            "Render a realistic concept image of the prototype's exterior appearance."
        ]
        image_urls = []
        for p in prompts:
            try:
                img_resp = _openai.images.generate(model="gpt-image-1", prompt=p, size="1024x1024")
                url = img_resp.data[0].url
                image_urls.append(url)
            except Exception:
                pass
        if image_urls:
            final_document += "\n\n## 4. Schematics & Visuals\n"
            for i, url in enumerate(image_urls, 1):
                final_document += f"\n**Figure {i}.**\n\n![]({url})\n"
    except Exception:
        pass

    return final_document


class SynthesizerAgent:
    """Lightweight agent wrapper for composing final proposals."""

    def __init__(self, model: str):
        self.model = model

    def run(self, idea: str, answers: Dict[str, str], include_simulations: bool = False) -> str:
        """Delegate to compose_final_proposal using the configured model."""
        return compose_final_proposal(idea, answers, include_simulations=include_simulations)
