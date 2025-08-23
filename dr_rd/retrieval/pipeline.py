from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .live_search import Source
from .vector_store import Retriever
from .context import fetch_context


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
    cfg_local = dict(cfg)
    cfg_local["retriever"] = retriever
    result = fetch_context(cfg_local, text, "pipeline", None)

    rag_snips = result["rag_snippets"]
    web_results = result["web_results"]
    meta = result["trace"]

    if web_results:
        summary = "\n".join(r.get("snippet", "") for r in web_results if r.get("snippet")) or None
        sources = [Source(title=r.get("title", ""), url=r.get("url")) for r in web_results]
    else:
        summary = None
        sources = []

    return ContextBundle(rag_snippets=rag_snips, web_summary=summary, sources=sources, meta=meta)
