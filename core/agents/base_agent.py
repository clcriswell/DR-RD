from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import streamlit as st
from utils.logging import logger

from config.feature_flags import (
    ENABLE_LIVE_SEARCH,
    LIVE_SEARCH_BACKEND,
    LIVE_SEARCH_MAX_CALLS,
    LIVE_SEARCH_SUMMARY_TOKENS,
    RAG_ENABLED,
    RAG_TOPK,
    VECTOR_INDEX_PATH,
)
from core.llm import complete
from core.llm_client import call_openai, log_usage
from core.prompt_utils import coerce_user_content
from dr_rd.retrieval.pipeline import collect_context
from dr_rd.retrieval.vector_store import Retriever, build_retriever


@dataclass(init=False)
class LLMRoleAgent:
    """Minimal LLM-backed agent used by the new orchestrator."""

    name: str
    model: str

    def __init__(self, name_or_model: str, model: Optional[str] = None):
        """Allow construction with either (name, model) or just model.

        If only a model is provided, derive the agent name from the class name by
        stripping a trailing 'Agent' and inserting spaces before capital letters
        (e.g. ``ResearchScientistAgent`` -> ``Research Scientist``).
        """

        if model is None:
            self.model = name_or_model
            role = type(self).__name__.removesuffix("Agent")
            self.name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", role)
        else:
            self.name = name_or_model
            self.model = model

    def act(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """Call the model with a system and user prompt."""
        user_prompt = coerce_user_content(user_prompt)
        system_prompt = coerce_user_content(system_prompt)
        chosen = model or self.model
        result = complete(system_prompt, user_prompt, model=chosen, **kwargs)
        return (result.content or "").strip()


# Backwards compatibility: legacy code imports `Agent` as the minimal LLM agent.
Agent = LLMRoleAgent

try:
    from dr_rd.retrieval.vector_store import Retriever
    from dr_rd.retrieval.vector_store import build_retriever as build_default_retriever
except Exception:  # pragma: no cover
    from dr_rd.retrieval.vector_store import Retriever  # type: ignore

    def build_default_retriever():  # type: ignore
        return None


class BaseAgent:
    """Base class for role-specific core.agents."""

    def __init__(
        self,
        name: str,
        model: str,
        system_message: str,
        user_prompt_template: str,
        retriever: Optional[Retriever] = None,
    ):
        self.name = name
        self.model = model
        self.system_message = system_message
        self.user_prompt_template = user_prompt_template
        if retriever is not None:
            self.retriever = retriever
        else:
            self.retriever = build_retriever(VECTOR_INDEX_PATH) if RAG_ENABLED else None
        self._sources: list[str] = []

    def _augment_prompt(
        self, prompt: str, idea: str, task: str, task_id: str = ""
    ) -> str:
        """Attach retrieved snippets and optionally web summary."""
        cfg = {
            "rag_enabled": RAG_ENABLED,
            "rag_top_k": RAG_TOPK,
            "live_search_enabled": ENABLE_LIVE_SEARCH,
            "live_search_backend": LIVE_SEARCH_BACKEND,
            "live_search_max_calls": LIVE_SEARCH_MAX_CALLS,
            "live_search_summary_tokens": LIVE_SEARCH_SUMMARY_TOKENS,
        }
        bundle = collect_context(idea, task, cfg, retriever=self.retriever)
        self._sources = bundle.sources or []
        logger.info(
            "RetrievalTrace agent=%s task_id=%s rag_hits=%d web_used=%s backend=%s sources=%d reason=%s",
            self.name,
            task_id,
            bundle.rag_hits,
            str(bundle.web_used).lower(),
            bundle.backend or "none",
            len(bundle.sources or []),
            bundle.reason or "n/a",
        )
        if bundle.rag_text:
            prompt += "\n\n# RAG Knowledge\n" + bundle.rag_text
        if bundle.web_summary:
            prompt += "\n\n# Web Search Results\n" + bundle.web_summary
            prompt += "\n\nIf you use Web Search Results, include a sources array in your JSON with short titles or URLs."
        return prompt

    def run(
        self,
        idea: str,
        task,
        design_depth: str = "Medium",
        *,
        model: str | None = None,
    ) -> str:
        """Construct the prompt and call the OpenAI API. Returns assistant text."""
        task_id = ""
        task_text = task
        if isinstance(task, dict):
            task_id = task.get("id", "")
            task_text = f"{task.get('title', '')}: {task.get('description', '')}"
        else:
            task_text = str(task)
        # Base prompt from template
        prompt = self.user_prompt_template.format(idea=idea, task=task_text)

        prompt = self._augment_prompt(prompt, idea, task_text, task_id)

        # Adjust prompt detail based on design_depth
        design_depth = design_depth.capitalize()  # normalize casing (Low/Medium/High)
        if design_depth == "High":
            prompt += (
                "\n\n**Design Depth: High** – Include all relevant component-level details. "
                "Provide exhaustive technical depth, with complete diagrams, schematics, and trade-off analyses for design decisions."
            )
        elif design_depth == "Low":
            prompt += (
                "\n\n**Design Depth: Low** – Provide a brief high-level overview with minimal technical detail. "
                "Focus on core concepts and avoid deep specifics or extensive diagrams."
            )
        else:  # Medium or default
            prompt += (
                "\n\n**Design Depth: Medium** – Provide a balanced level of detail. "
                "Include key diagrams or specifications and reasoning for major decisions without delving into excessive minutiae."
            )

        # Call OpenAI via llm_client
        model_id = model or self.model
        logger.info(f"Model[exec]={model_id} params={{}}")
        result = call_openai(
            model=model_id,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        )
        resp = result["raw"]
        usage = getattr(resp, "usage", None)
        if usage is None and getattr(resp, "choices", None):
            usage = getattr(resp.choices[0], "usage", None)
        if usage:
            log_usage(
                stage="exec",
                model=model_id,
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        answer = (result["text"] or "").strip()
        flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
        if flags.get("TEST_MODE"):
            max_chars = int(flags.get("MAX_OUTPUT_CHARS", 900))
            if isinstance(answer, str) and len(answer) > max_chars:
                answer = answer[:max_chars] + " …[truncated test]"
        if self._sources:
            try:
                data = json.loads(answer)
                data.setdefault("sources", self._sources)
                answer = json.dumps(data)
            except Exception:
                pass
        return answer
