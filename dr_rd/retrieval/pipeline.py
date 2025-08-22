from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .vector_store import Snippet, Retriever, build_retriever
from .live_search import get_live_client
from core.llm_client import BUDGET

@dataclass
class ContextBundle:
    rag_text: str = ""
    web_summary: str = ""
    sources: List[str] | None = None
    rag_hits: int = 0
    web_used: bool = False
    backend: str | None = None
    reason: str | None = None


def collect_context(idea: str, task: str, cfg: dict, retriever: Optional[Retriever] = None) -> ContextBundle:
    sources: List[str] = []
    text = f"{idea}\n{task}".strip()
    retriever = retriever or build_retriever()
    rag_text = ""
    hits: List[Snippet] = []
    reason = None
    if cfg.get("rag_enabled") and retriever:
        try:
            hits = retriever.query(text, cfg.get("rag_top_k", 5))  # type: ignore[arg-type]
        except Exception:
            hits = []
        if hits:
            rag_text = "\n".join(sn.text for sn in hits)
            sources.extend(sn.source for sn in hits)
            if BUDGET:
                BUDGET.retrieval_calls += 1
                BUDGET.retrieval_tokens += sum(len(sn.text.split()) for sn in hits)
    else:
        if not cfg.get("rag_enabled"):
            reason = "rag_disabled"
        elif not retriever:
            reason = "no_index"
    rag_hits = len(hits)
    web_summary = ""
    web_used = False
    backend = None
    if cfg.get("live_search_enabled") and rag_hits < 1:
        backend = cfg.get("live_search_backend", "openai")
        max_calls = int(cfg.get("live_search_max_calls", 0))
        if BUDGET and BUDGET.web_search_calls >= max_calls > 0:
            BUDGET.skipped_due_to_budget = getattr(BUDGET, "skipped_due_to_budget", 0) + 1
            reason = "budget"
        else:
            client = get_live_client(backend)
            summary, srcs = client.search_and_summarize(
                text,
                cfg.get("rag_top_k", 5),
                cfg.get("live_search_summary_tokens", 256),
            )
            web_summary = summary
            sources.extend([s.title or (s.url or "") for s in srcs])
            web_used = True
            if BUDGET:
                BUDGET.web_search_calls += 1
    elif not cfg.get("live_search_enabled"):
        reason = reason or "web_disabled"
    elif rag_hits >= 1:
        reason = reason or "rag_sufficient"
    return ContextBundle(
        rag_text=rag_text,
        web_summary=web_summary,
        sources=sources,
        rag_hits=rag_hits,
        web_used=web_used,
        backend=backend,
        reason=reason,
    )
