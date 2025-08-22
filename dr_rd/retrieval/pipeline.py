from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .vector_store import Snippet, Retriever, build_retriever
from .live_search import get_live_client, Source
from core.llm_client import BUDGET

@dataclass
class ContextBundle:
    rag_text: str = ""
    web_summary: str = ""
    sources: List[str] | None = None


def collect_context(idea: str, task: str, cfg: dict, retriever: Optional[Retriever] = None) -> ContextBundle:
    sources: List[str] = []
    text = f"{idea}\n{task}".strip()
    retriever = retriever or build_retriever()
    rag_text = ""
    hits: List[Snippet] = []
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
    web_summary = ""
    if cfg.get("live_search_enabled") and len(hits) < 1:
        backend = cfg.get("live_search_backend", "openai")
        max_calls = int(cfg.get("live_search_max_calls", 0))
        if BUDGET and BUDGET.web_search_calls >= max_calls > 0:
            BUDGET.skipped_due_to_budget = getattr(BUDGET, "skipped_due_to_budget", 0) + 1
        else:
            client = get_live_client(backend)
            summary, srcs = client.search_and_summarize(text, cfg.get("rag_top_k",5), cfg.get("live_search_summary_tokens",256))
            web_summary = summary
            sources.extend([s.title or (s.url or "") for s in srcs])
            if BUDGET:
                BUDGET.web_search_calls += 1
    return ContextBundle(rag_text=rag_text, web_summary=web_summary, sources=sources)
