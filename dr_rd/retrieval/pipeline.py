from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.llm_client import BUDGET
from core.retrieval import budget as retrieval_budget

from .live_search import Source, get_live_client
from .vector_store import Retriever, Snippet


@dataclass
class ContextBundle:
    """Container of retrieved context for prompt augmentation."""

    rag_snippets: List[str]
    web_summary: str | None
    sources: List[Source]
    meta: Dict[str, object]


def collect_context(
    idea: str, task_text: str, cfg: dict, retriever: Optional[Retriever] = None
) -> ContextBundle:
    """Gather vector and live-search context for a task."""

    text = f"{idea}\n{task_text}".strip()

    rag_hits = 0
    rag_snips: List[str] = []
    sources: List[Source] = []
    reason = "ok"

    if cfg.get("rag_enabled") and retriever is not None:
        try:
            hits = retriever.query(text, cfg.get("rag_top_k", 5))  # type: ignore[arg-type]
        except Exception:
            hits = []
            reason = "error"
        rag_hits = len(hits)
        if rag_hits:
            rag_snips = [sn.text for sn in hits]
            sources.extend(Source(title=sn.source, url=None) for sn in hits)
            if BUDGET:
                BUDGET.retrieval_calls += 1
                BUDGET.retrieval_tokens += sum(len(sn.text.split()) for sn in hits)
        else:
            reason = "no_results"
    else:
        if not cfg.get("vector_index_present", False):
            reason = "no_vector"
        else:
            reason = "rag_disabled"

    budget = retrieval_budget.RETRIEVAL_BUDGET
    budget_allows = budget.allow() if budget else True
    need_web = (not cfg.get("vector_index_present", False)) or rag_hits == 0
    should_try_web = cfg.get("live_search_enabled", False) and budget_allows and need_web

    web_summary: str | None = None
    web_used = False
    backend = "none"
    web_sources_count = 0

    if should_try_web:
        backend = cfg.get("live_search_backend", "openai")
        try:
            client = get_live_client(backend)
            summary, srcs = client.search_and_summarize(
                text,
                cfg.get("rag_top_k", 5),
                cfg.get("live_search_summary_tokens", 256),
            )
            web_summary = summary
            sources.extend(srcs)
            web_sources_count = len(srcs)
            web_used = True
            if budget:
                budget.consume()
            if BUDGET:
                BUDGET.web_search_calls += 1
            reason = (
                "fallback_no_vector"
                if not cfg.get("vector_index_present", False)
                else "no_results"
            )
        except Exception:
            reason = "error"
    else:
        if need_web and cfg.get("live_search_enabled", False) and not budget_allows:
            reason = "budget_exhausted"
            if BUDGET:
                BUDGET.skipped_due_to_budget = getattr(
                    BUDGET, "skipped_due_to_budget", 0
                ) + 1
        elif not cfg.get("vector_index_present", False):
            reason = "no_vector"
        elif rag_hits == 0:
            reason = "no_results"
        else:
            reason = "ok"

    meta = {
        "rag_hits": rag_hits,
        "web_used": web_used,
        "backend": backend if web_used else "none",
        "sources": web_sources_count if web_used else 0,
        "reason": reason,
    }

    return ContextBundle(
        rag_snippets=rag_snips,
        web_summary=web_summary,
        sources=sources,
        meta=meta,
    )
