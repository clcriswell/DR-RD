"""
Prototype Synthesizer / Final Composer
--------------------------------------
Combines the user's original idea with the (optionally loop-refined)
multi-domain answers to draft a cohesive, testable design or development
plan.  Returns Markdown text ready for Streamlit rendering.

Call:
    from core.agents.synthesizer_agent import synthesize
    markdown = synthesize(user_idea, answers_dict)
"""
from typing import Dict
import logging
import os
import streamlit as st

from config.feature_flags import ENABLE_IMAGES

from core.llm import complete, select_model
from core.llm_client import BUDGET, log_usage
from utils.image_visuals import make_visuals_for_project
from core.retrieval.budget import RETRIEVAL_BUDGET
from prompts.prompts import (
    SYNTHESIZER_TEMPLATE,
    SYNTHESIZER_BUILD_GUIDE_TEMPLATE,
)

def synthesize(idea: str, answers: Dict[str, str], model: str | None = None) -> str:
    findings_md = "\n".join(f"### {d}\n{answers[d]}" for d in answers)
    prompt = SYNTHESIZER_TEMPLATE.format(idea=idea, findings_md=findings_md)

    model_id = model or select_model("agent", agent_name="Synthesizer")
    logging.info(f"Model[synth]={model_id}")
    result = complete(
        "You are an expert R&D writer.",
        prompt,
        model=model_id,
        temperature=0.3,
    )
    usage = result.raw.get("usage") if isinstance(result.raw, dict) else getattr(result.raw, "usage", None)
    if usage:
        log_usage(
            stage="synth",
            model=model_id,
            pt=getattr(usage, "prompt_tokens", 0),
            ct=getattr(usage, "completion_tokens", 0),
        )
    return (result.content or "").strip()


def compose_final_proposal(
    idea: str,
    answers: Dict[str, str],
    include_simulations: bool = False,
    model: str | None = None,
):
    """Compose a Prototype Build Guide integrating agent contributions."""
    model_id = model or select_model("agent", agent_name="Synthesizer")
    logging.info(f"Model[synth]={model_id}")
    contributions = "\n".join(f"### {role}\n{content}" for role, content in answers.items())
    sections = [
        "1. Executive Summary",
        "2. Bill of Materials (as a table)",
        "3. Step-by-Step Instructions (numbered, with reasoning)",
    ]
    if include_simulations:
        sections.append("4. Simulation & Test Results (if available)")
    prompt = SYNTHESIZER_BUILD_GUIDE_TEMPLATE.format(
        sections="\n".join(sections),
        idea=idea,
        contributions=contributions,
    )
    result = complete(
        "You are an expert R&D writer.",
        prompt,
        model=model_id,
    )
    usage = result.raw.get("usage") if isinstance(result.raw, dict) else getattr(result.raw, "usage", None)
    if usage:
        log_usage(
            stage="synth",
            model=model_id,
            pt=getattr(usage, "prompt_tokens", 0),
            ct=getattr(usage, "completion_tokens", 0),
        )
    final_document = result.content

    flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
    try:
        plan_roles = list(answers.keys()) if isinstance(answers, dict) else None
    except Exception:
        plan_roles = None
    bucket = os.environ.get("GCS_BUCKET") or os.environ.get("GCS_IMAGES_BUCKET")
    images = []
    if not flags.get("ENABLE_IMAGES", ENABLE_IMAGES):
        if not getattr(compose_final_proposal, "_image_disabled_logged", False):
            logging.info("Images: skipped (disabled by config)")
            compose_final_proposal._image_disabled_logged = True
    elif flags.get("TEST_MODE"):
        img_size = flags.get("IMAGES_SIZE", "256x256")
        img_quality = flags.get("IMAGES_QUALITY", "high")
        try:
            from utils.image_visuals import _openai as _img_openai, _decode_to_bytes, upload_bytes_to_gcs
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
            url = None
            if bucket:
                filename = f"{int(__import__('time').time())}-test.{fmt}"
                try:
                    url = upload_bytes_to_gcs(bio.getvalue(), filename, content_type, bucket)
                except Exception:
                    url = None
            images.append({"kind": "test", "url": url, "data": bio.getvalue(), "caption": "Test Visual"})
        except Exception:
            pass
    else:
        images = make_visuals_for_project(idea, plan_roles, bucket)

    if images:
        final_document += "\n\n## 4. Schematics & Visuals\n"
        for i, img in enumerate(images, 1):
            final_document += f"\n**Figure {i}. {img['caption']}**\n"
            if img.get("url"):
                final_document += f"\n![]({img['url']})\n"

    result_payload = {"document": final_document, "images": images, "test": bool(flags.get("TEST_MODE"))}
    if not getattr(compose_final_proposal, "_budget_logged", False):
        used = RETRIEVAL_BUDGET.used if RETRIEVAL_BUDGET else 0
        cap = RETRIEVAL_BUDGET.max_calls if RETRIEVAL_BUDGET else 0
        logging.info(
            "RetrievalBudget web_search_calls=%d/%d",
            used,
            cap,
        )
        compose_final_proposal._budget_logged = True
    return result_payload


class SynthesizerAgent:
    """Lightweight agent wrapper for composing final proposals."""

    def __init__(self, model: str):
        self.model = model

    def run(
        self,
        idea: str,
        answers: Dict[str, str],
        include_simulations: bool = False,
        *,
        model: str | None = None,
    ):
        """Delegate to compose_final_proposal using the configured model."""
        return compose_final_proposal(
            idea,
            answers,
            include_simulations=include_simulations,
            model=model or self.model,
        )
