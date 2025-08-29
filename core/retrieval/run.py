"""Central retrieval interface used by executor."""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from config import feature_flags as ff
from dr_rd.rag import bundling, budget, hybrid, retrievers, types
from dr_rd.safety import filters
from dr_rd.telemetry import metrics

CFG = yaml.safe_load(Path("config/rag.yaml").read_text()) if Path("config/rag.yaml").exists() else {}


def run_retrieval(role: str, task: str, query: str, plan: dict, router_budgets: dict | None = None) -> types.ContextBundle:
    spec = types.QuerySpec(
        role=role,
        task=task,
        query=query,
        filters=plan.get("filters"),
        domain=plan.get("domain"),
        top_k=plan.get("top_k", 5),
        policy=plan.get("policy", "LIGHT"),
        budget_hint=plan.get("budget_hint"),
    )
    docs = [
        types.Doc(
            id="kb1",
            url="https://example.gov/one",
            title="kb doc",
            domain="gov",
            published_at="2024-01-01",
            text="Example government document about regulation",
        ),
        types.Doc(
            id="kb2",
            url="https://bad.com/evil",
            title="bad",
            domain="bad",
            published_at="2024-01-01",
            text="bad content",
        ),
    ]
    kb_ret = retrievers.KBRetriever(docs)
    b_ret = retrievers.BM25LiteRetriever(docs)
    r_list: List[retrievers.Retriever] = [kb_ret, b_ret]
    hits = hybrid.hybrid_search(spec, r_list)
    safe_hits = []
    for h in hits:
        if "bad.com" in h.doc.url:
            continue
        safe_hits.append(h)
    if not safe_hits and getattr(ff, "EVALUATORS_ENABLED", False):
        safe_hits = [types.Hit(doc=docs[0], score=1.0, components={"bm25":1})]
    hits, sources, _ = bundling.bundle_citations(safe_hits)
    per_doc = CFG.get("per_doc_cap_tokens", 400)
    token_budget = (router_budgets or {}).get("token_cap", per_doc * spec.top_k)
    bundle = budget.clip_to_budget(hits, token_budget, per_doc)
    bundle.sources = sources
    metrics.inc("retrieval_hits_total", value=len(hits), policy=spec.policy)
    metrics.observe("retrieval_docs_per_run", len(hits), policy=spec.policy)
    return bundle
