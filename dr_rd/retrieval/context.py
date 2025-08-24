from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
import os

from core.llm_client import BUDGET
from core.retrieval import budget as rbudget
from core.retrieval.budget import get_web_search_call_cap
from dr_rd.retrieval.live_search import (
    get_live_client,
    OpenAIWebSearchClient,
    OpenAIWebSearchUnavailable,
)
from dr_rd.retrieval.vector_store import Retriever
from utils.search_tools import search_google

log = logging.getLogger("drrd")


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
            backend = "openai"
            web_used = True
            try:
                client = get_live_client("openai")
                extra = {}
                if isinstance(client, OpenAIWebSearchClient):
                    extra = {
                        "tools": [{"type": "web_search_preview"}],
                        "tool_choice": "required",
                    }
                try:
                    _summary, srcs = client.search_and_summarize(
                        query,
                        rag_top_k,
                        cfg.get("live_search_summary_tokens", 256),
                        **extra,
                    )
                except TypeError:
                    _summary, srcs = client.search_and_summarize(
                        query,
                        rag_top_k,
                        cfg.get("live_search_summary_tokens", 256),
                    )
                web_results = [
                    {"title": s.title, "url": s.url or "", "snippet": ""} for s in srcs
                ]
                cfg["web_search_calls_used"] = used + 1
                if budget_obj:
                    budget_obj.consume()
                if BUDGET:
                    BUDGET.web_search_calls += 1
            except OpenAIWebSearchUnavailable as e:
                log.warning(
                    "RetrievalTrace agent=%s task_id=%s rag_hits=%d web_used=false backend=openai sources=0 reason=live_search_error err=%s",
                    agent_name,
                    task_id,
                    rag_hits,
                    e,
                )
                web_used = False
                reason = "live_search_error"
                serp_key = os.getenv("SERPAPI_KEY")
                if str(cfg.get("live_search_backend")) == "serpapi" and serp_key:
                    backend = "serpapi"
                    raw = search_google(agent_name, "", query, k=rag_top_k)
                    web_results = _format_results(raw)
                    web_used = True
                    cfg["web_search_calls_used"] = used + 1
                    if budget_obj:
                        budget_obj.consume()
                    if BUDGET:
                        BUDGET.web_search_calls += 1
            except Exception as e:
                log.warning(
                    "RetrievalTrace agent=%s task_id=%s rag_hits=%d web_used=false backend=openai sources=0 reason=live_search_error err=%s",
                    agent_name,
                    task_id,
                    rag_hits,
                    e,
                )
                web_used = False
                reason = "live_search_error"
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
        "backend": backend,
        "sources": len(web_results),
        "reason": reason,
    }

    return {"rag_snippets": rag_snips, "web_results": web_results, "trace": trace}


def retrieve_context(
    idea: str,
    config: Dict[str, Any],
    index,
) -> Dict[str, Any]:
    """Simplified context retriever used by tests and lightweight callers."""

    rag_enabled = bool(config.get("rag_enabled", True))
    live_enabled = bool(config.get("live_search_enabled", True))
    backend = (config.get("live_search_backend") or "openai").lower()

    max_calls = config.get("web_search_max_calls")
    if max_calls in (None, "", 0):
        max_calls = config.get("live_search_max_calls")
    try:
        max_calls = int(max_calls) if max_calls not in (None, "") else None
    except Exception:
        max_calls = None
    if max_calls is None:
        max_calls = 3 if (not getattr(index, "present", False)) else 0

    used_calls = 0
    snippets: List[Dict[str, str]] = []
    web_summary = None
    web_sources: List[Dict[str, str]] = []

    need_web = False
    if rag_enabled and getattr(index, "present", False):
        vec = index.search(idea, k=int(config.get("rag_top_k") or 5))
        snippets.extend(vec or [])
        need_web = not snippets
    else:
        need_web = True

    if live_enabled and need_web and used_calls < max_calls:
        try:
            res = run_live_search_with_fallback(
                query=idea,
                llm_model=(
                    config.get("exec_model")
                    or config.get("synth_model")
                    or "gpt-4.1-mini"
                ),
                backend_primary=backend,
                allow_serpapi_fallback=True,
                max_sources=5,
            )
            web_summary = res.get("text") or ""
            web_sources = list(res.get("sources") or [])
            used_calls += 1
            log.info(
                "RetrievalTrace agent=live_search rag_hits=%d web_used=true backend=%s sources=%d reason=%s",
                len(snippets),
                backend,
                len(web_sources),
                "forced_no_vector" if not getattr(index, "present", False) else "no_vec_hits",
            )
        except Exception as e:  # pragma: no cover - network failures
            log.warning(
                "RetrievalTrace agent=live_search rag_hits=%d web_used=false backend=%s sources=0 reason=live_search_error err=%s",
                len(snippets),
                backend,
                e,
            )

    meta = {
        "rag_enabled": rag_enabled,
        "live_enabled": live_enabled,
        "backend": backend,
        "web_search_calls_used": used_calls,
        "web_search_max_calls": int(max_calls or 0),
        "vector_index_present": bool(getattr(index, "present", False)),
    }
    return {
        "snippets": snippets,
        "web_summary": web_summary,
        "web_sources": web_sources,
        "meta": meta,
    }
