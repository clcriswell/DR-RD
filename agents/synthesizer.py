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
import os
import streamlit as st
from dr_rd.utils.image_visuals import make_visuals_for_project

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


def compose_final_proposal(idea: str, answers: Dict[str, str], include_simulations: bool = False):
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

    flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
    try:
        plan_roles = list(answers.keys()) if isinstance(answers, dict) else None
    except Exception:
        plan_roles = None
    bucket = os.environ.get("GCS_BUCKET") or os.environ.get("GCS_IMAGES_BUCKET")
    images = []
    if flags.get("TEST_MODE"):
        img_size = flags.get("IMAGES_SIZE", "1024x1024")
        img_quality = flags.get("IMAGES_QUALITY", "high")
        try:
            from dr_rd.utils.image_visuals import _openai as _img_openai, _decode_to_bytes, upload_bytes_to_gcs
            client = _img_openai()
            prompt = f"Schematic/appearance concept for dev test: {idea[:160]}"
            res = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=img_size,
                quality=img_quality,
                n=1,
            )
            b64 = res.data[0].b64_json
            data = _decode_to_bytes(b64)
            from io import BytesIO
            bio = BytesIO(data)
            fmt = "png"
            content_type = "image/png"
            if bucket:
                filename = f"{int(__import__('time').time())}-test.{fmt}"
                try:
                    url = upload_bytes_to_gcs(bio.getvalue(), filename, content_type, bucket)
                except Exception:
                    url = f"data:{content_type};base64,{b64}"
            else:
                url = f"data:{content_type};base64,{b64}"
            images.append({"kind": "test", "url": url, "caption": "Test Visual"})
        except Exception:
            pass
    else:
        images = make_visuals_for_project(idea, plan_roles, bucket)

    if images:
        final_document += "\n\n## 4. Schematics & Visuals\n"
        for i, img in enumerate(images, 1):
            final_document += f"\n**Figure {i}. {img['caption']}**\n\n![]({img['url']})\n"

    result_payload = {"document": final_document, "images": images, "test": bool(flags.get("TEST_MODE"))}
    return result_payload


class SynthesizerAgent:
    """Lightweight agent wrapper for composing final proposals."""

    def __init__(self, model: str):
        self.model = model

    def run(self, idea: str, answers: Dict[str, str], include_simulations: bool = False):
        """Delegate to compose_final_proposal using the configured model."""
        return compose_final_proposal(idea, answers, include_simulations=include_simulations)
