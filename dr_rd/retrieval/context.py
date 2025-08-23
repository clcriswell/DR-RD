from __future__ import annotations

import json
from typing import Any, Dict, List

from core.llm_client import BUDGET
from core.retrieval import budget as rbudget
from core.retrieval.budget import get_web_search_call_cap
from dr_rd.retrieval.live_search import get_live_client
from dr_rd.retrieval.vector_store import Retriever
from utils.search_tools import search_google


def _format_results(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for r in results:
        out.append(
            {
                "title": str(r.get("title", "")),
                "url": str(r.get("link") or r.get("url") or ""),
                "snippet": str(r.get("snippet", "")),
            }
        )
    return out


def fetch_context(
    cfg: Dict[str, Any], query: str, agent_name: str, task_id: str | None
) -> Dict[str, Any]:
    """Retrieve vector and/or web context for a query."""

    retriever: Retriever | None = cfg.get("retriever")
    rag_enabled = bool(cfg.get("rag_enabled")) and bool(
        cfg.get("vector_index_present")
    )
    rag_top_k = int(cfg.get("rag_top_k", 5))

    rag_snips: List[str] = []
    rag_hits = 0
    if rag_enabled and retriever is not None:
        try:
            hits = retriever.query(query, rag_top_k)
        except Exception:
            hits = []
        rag_hits = len(hits)
        rag_snips = [getattr(h, "text", str(h)) for h in hits]
        if BUDGET and rag_hits:
            BUDGET.retrieval_calls += 1
            BUDGET.retrieval_tokens += sum(len(s.split()) for s in rag_snips)

    vector_present = bool(cfg.get("vector_index_present"))
    reason = "ok"
    need_web = False
    if not vector_present:
        reason = "web_only_mode"
        need_web = True
    elif rag_hits == 0:
        reason = "rag_zero_hits"
        need_web = True

    max_calls = get_web_search_call_cap(cfg)
    cfg.setdefault("web_search_max_calls", max_calls)
    used = int(cfg.get("web_search_calls_used", 0))
    budget_obj = rbudget.RETRIEVAL_BUDGET
    budget_allows = used < max_calls and (budget_obj.allow() if budget_obj else True)

    web_results: List[Dict[str, str]] = []
    web_used = False
    backend = "none"

    if need_web:
        if cfg.get("live_search_enabled") and budget_allows:
            backend = str(cfg.get("live_search_backend", "openai"))
            try:
                if backend == "serpapi":
                    raw = search_google(agent_name, "", query, k=rag_top_k)
                    web_results = _format_results(raw)
                else:
                    client = get_live_client(backend)
                    _summary, srcs = client.search_and_summarize(
                        query, rag_top_k, cfg.get("live_search_summary_tokens", 256)
                    )
                    web_results = [
                        {"title": s.title, "url": s.url or "", "snippet": ""} for s in srcs
                    ]
                web_used = True
                cfg["web_search_calls_used"] = used + 1
                if budget_obj:
                    budget_obj.consume()
                if BUDGET:
                    BUDGET.web_search_calls += 1
            except Exception:
                pass
        else:
            if not cfg.get("live_search_enabled"):
                reason = "disabled"
            elif not budget_allows:
                reason = "budget_exhausted"
                if BUDGET:
                    BUDGET.skipped_due_to_budget += 1

    trace = {
        "rag_hits": rag_hits,
        "web_used": web_used,
        "backend": backend if web_used else "none",
        "sources": len(web_results),
        "reason": reason,
    }

    return {"rag_snippets": rag_snips, "web_results": web_results, "trace": trace}
