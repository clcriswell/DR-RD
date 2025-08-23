from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.llm_client import BUDGET

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

    if cfg.get("rag_enabled"):
        if retriever is not None:
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
                reason = "rag_empty"
        else:
            reason = "no_retriever"
    else:
        reason = "disabled_in_mode"

    web_summary: str | None = None
    web_used = False
    backend = None
    if cfg.get("live_search_enabled") and (rag_hits == 0 or retriever is None):
        backend = cfg.get("live_search_backend", "openai")
        max_calls = int(cfg.get("live_search_max_calls", 0))
        if BUDGET and BUDGET.web_search_calls >= max_calls > 0:
            BUDGET.skipped_due_to_budget = getattr(BUDGET, "skipped_due_to_budget", 0) + 1
            reason = "budget_skip"
        else:
            try:
                client = get_live_client(backend)
                summary, srcs = client.search_and_summarize(
                    text,
                    cfg.get("rag_top_k", 5),
                    cfg.get("live_search_summary_tokens", 256),
                )
                web_summary = summary
                sources.extend(srcs)
                web_used = True
                if BUDGET:
                    BUDGET.web_search_calls += 1
            except Exception:
                reason = "error"

    meta = {
        "rag_hits": rag_hits,
        "web_used": web_used,
        "backend": backend or "none",
        "reason": reason,
    }
    return ContextBundle(rag_snippets=rag_snips, web_summary=web_summary, sources=sources, meta=meta)
