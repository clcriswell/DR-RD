from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Tuple
import re

from config.feature_flags import (
    RAG_ENABLED,
    RAG_TOPK,
    ENABLE_LIVE_SEARCH,
)
import logging
import streamlit as st
from dr_rd.llm_client import call_openai
from dr_rd.utils.llm_client import log_usage
from core.llm import complete
from dr_rd.core.prompt_utils import coerce_user_content

logger = logging.getLogger(__name__)


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

    def act(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call the model with a system and user prompt."""
        user_prompt = coerce_user_content(user_prompt)
        system_prompt = coerce_user_content(system_prompt)
        result = complete(system_prompt, user_prompt, model=self.model, **kwargs)
        return (result.content or "").strip()

try:  # avoid import errors when knowledge package is absent
    from dr_rd.knowledge.retriever import Retriever
    from dr_rd.knowledge.faiss_store import build_default_retriever
except Exception:  # pragma: no cover - fallback when module missing
    Retriever = None  # type: ignore
    build_default_retriever = lambda: None  # type: ignore


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
        if RAG_ENABLED and retriever is None:
            try:
                self.retriever: Optional[Retriever] = build_default_retriever()
            except Exception:  # pragma: no cover - best effort
                self.retriever = None
        else:
            self.retriever = retriever
        self.retrieval_hits = 0
        self.rag_text_len = 0
        self._web_summary: str | None = None
        self._web_sources: list[str] = []

    def _augment_prompt(self, prompt: str, idea: str, task: str) -> str:
        """Attach retrieved snippets and optionally web summary."""
        context = f"{idea}\n{task}"
        hits: List[Tuple[str, str]] = []
        if RAG_ENABLED and self.retriever:
            try:
                hits = self.retriever.query(context, RAG_TOPK)
            except Exception:
                hits = []
        self.retrieval_hits = len(hits)
        self.rag_text_len = sum(len(t.split()) for t, _ in hits)
        if hits:
            bundle_lines = []
            for i, (text, src) in enumerate(hits, 1):
                raw = text.replace("\n", " ")
                bundle_lines.append(f"[{i}] {raw} ({src})")
            bundle = "\n".join(bundle_lines)
            print(f"[RAG] {self.name} retrieved {len(hits)} snippet(s)")
            prompt += "\n\n# RAG Knowledge\n" + bundle

        self._web_summary = None
        self._web_sources = []
        self.maybe_live_search(idea, task)
        if self._web_summary:
            prompt += "\n\n# Web Search Results\n" + self._web_summary
            prompt += (
                "\n\nIf you use Web Search Results, include a sources array in your JSON with short titles or URLs."
            )
        return prompt

    def maybe_live_search(self, idea: str, task: str) -> None:
        if not ENABLE_LIVE_SEARCH:
            return
        if not (
            self.retrieval_hits == 0 or self.rag_text_len < 50
        ):
            return
        try:
            from utils.search_tools import (
                search_google,
                summarize_search,
                obfuscate_query,
            )

            query = obfuscate_query(self.name, idea, task)
            results = search_google(query, k=5)
            if not results:
                return
            summary = summarize_search([r.get("snippet", "") for r in results])
            if summary:
                self._web_summary = summary
                self._web_sources = [
                    r.get("title") or r.get("link") or "" for r in results
                ][:5]
        except Exception:
            return

    def run(self, idea: str, task, design_depth: str = "Medium") -> str:
        """Construct the prompt and call the OpenAI API. Returns assistant text."""
        if isinstance(task, dict):
            task = f"{task.get('title', '')}: {task.get('description', '')}"
        # Base prompt from template
        prompt = self.user_prompt_template.format(idea=idea, task=task)

        prompt = self._augment_prompt(prompt, idea, task)

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
        from core.agents.unified_registry import resolve_model  # local import to avoid circular
        model_id = self.model or resolve_model(self.name)
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
        return answer

