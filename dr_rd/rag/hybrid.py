"""Hybrid lexical+dense ranking and dedupe."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from . import quality
from .types import Doc, Hit, QuerySpec

CFG = quality.CFG
WEIGHTS = CFG.get("weights", {"bm25": 0.45, "dense": 0.35, "quality": 0.20})


def _normalise(scores: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    norm: Dict[str, Dict[str, float]] = {}
    for comp, vals in scores.items():
        if not vals:
            continue
        mx = max(vals) or 1.0
        mn = min(vals)
        denom = mx - mn or 1.0
        norm[comp] = {str(i): (v - mn) / denom for i, v in enumerate(vals)}
    return norm


def hybrid_search(spec: QuerySpec, retrievers: Iterable) -> List[Hit]:
    all_docs: Dict[str, Doc] = {}
    comp_scores: Dict[str, Dict[str, float]] = defaultdict(dict)
    doc_list: List[Doc] = []
    for idx, r in enumerate(retrievers):
        docs = r.search(spec)
        for rank, doc in enumerate(docs):
            key = doc.url
            if key not in all_docs:
                all_docs[key] = doc
                doc_list.append(doc)
            comp_scores[r.name][key] = doc.meta.get("score", 0.0)
    # quality
    quality_scores = {}
    for doc in doc_list:
        q = quality.score_source(doc, spec.query)
        quality_scores[doc.url] = q
        comp_scores["quality"][doc.url] = q
    # normalise
    comp_norm = {}
    for comp, d in comp_scores.items():
        vals = list(d.values())
        mx = max(vals) or 1.0
        mn = min(vals)
        denom = mx - mn or 1.0
        comp_norm[comp] = {k: (v - mn) / denom for k, v in d.items()}
    hits: List[Hit] = []
    for url, doc in all_docs.items():
        fused = 0.0
        components: Dict[str, float] = {}
        for comp, weight in WEIGHTS.items():
            val = comp_norm.get(comp, {}).get(url, 0.0)
            fused += weight * val
            components[comp] = val
        hits.append(Hit(doc=doc, score=fused, components=components))
    hits.sort(key=lambda h: h.score, reverse=True)
    for i, h in enumerate(hits, 1):
        h.rank = i
    return hits[: spec.top_k]
