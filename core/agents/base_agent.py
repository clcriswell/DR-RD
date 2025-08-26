from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import streamlit as st
from utils.logging import logger

from config.feature_flags import (
    LIVE_SEARCH_SUMMARY_TOKENS,
    RAG_ENABLED,
    RAG_TOPK,
    VECTOR_INDEX_PATH,
    VECTOR_INDEX_PRESENT,
)
import config.feature_flags as ff
from core.llm import complete
from core.llm_client import call_openai, log_usage
from core.prompt_utils import coerce_user_content
from dr_rd.retrieval.context import fetch_context
from dr_rd.retrieval.vector_store import Retriever, build_retriever
from core.retrieval import budget as rbudget
from core.agents.tool_use import ToolUseMixin


@dataclass(init=False)
class LLMRoleAgent(ToolUseMixin):
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
            self.retriever = (
                build_retriever(VECTOR_INDEX_PATH) if RAG_ENABLED and VECTOR_INDEX_PRESENT else None
            )
        self._sources: list[str] = []

    def _augment_prompt(self, prompt: str, idea: str, task: str, task_id: str = "") -> str:
        """Attach retrieved snippets and optionally web summary."""
        vector_available = VECTOR_INDEX_PRESENT and self.retriever is not None
        cfg = {
            "rag_enabled": RAG_ENABLED and vector_available,
            "rag_top_k": RAG_TOPK,
            "live_search_enabled": ff.ENABLE_LIVE_SEARCH,
            "live_search_backend": ff.LIVE_SEARCH_BACKEND,
            "live_search_summary_tokens": LIVE_SEARCH_SUMMARY_TOKENS,
            "vector_index_present": vector_available,
            "retriever": self.retriever,
            "live_search_max_calls": ff.LIVE_SEARCH_MAX_CALLS,
        }
        ctx = fetch_context(cfg, f"{idea}\n{task}".strip(), self.name, task_id)
        trace = ctx["trace"]
        self._sources = [r.get("title") or r.get("url", "") for r in ctx.get("web_results", [])]
        logger.info(
            "RetrievalTrace agent=%s task_id=%s rag_hits=%d web_used=%s backend=%s sources=%d reason=%s",
            self.name,
            task_id,
            trace.get("rag_hits", 0),
            str(trace.get("web_used", False)).lower(),
            trace.get("backend", "none"),
            trace.get("sources", 0),
            trace.get("reason", "ok"),
        )
        if ctx.get("rag_snippets"):
            prompt += "\n\n# RAG Knowledge\n" + "\n".join(ctx["rag_snippets"])
        if ctx.get("web_results"):
            prompt += "\n\n# Web Search Results\n"
            for res in ctx["web_results"]:
                title = res.get("title", "")
                snippet = res.get("snippet", "")
                url = res.get("url", "")
                line = f"- {title}: {snippet} ({url})".strip()
                prompt += line + "\n"
            prompt += "\nIf you use Web Search Results, include a sources array in your JSON with short titles or URLs."
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
            enable_web_search=ff.ENABLE_LIVE_SEARCH,
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
        used = rbudget.RETRIEVAL_BUDGET.used if rbudget.RETRIEVAL_BUDGET else 0
        cap = rbudget.RETRIEVAL_BUDGET.max_calls if rbudget.RETRIEVAL_BUDGET else 0
        logger.info("RetrievalBudget web_search_calls=%d/%d", used, cap)
        answer = (result["text"] or "").strip()
        if self._sources:
            try:
                data = json.loads(answer)
                data.setdefault("sources", self._sources)
                answer = json.dumps(data)
            except Exception:
                pass
        return answer
