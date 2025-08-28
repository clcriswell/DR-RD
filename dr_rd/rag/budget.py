"""Token budget clipping."""

from __future__ import annotations

from typing import List

from .types import ContextBundle, Hit


def _estimate_tokens(text: str) -> int:
    return max(len(text) // 4, 1)


def clip_to_budget(hits: List[Hit], token_budget: int, per_doc_token_cap: int) -> ContextBundle:
    kept: List[Hit] = []
    sources: List[dict] = []
    total = 0
    for hit in hits:
        text = hit.doc.text
        est = _estimate_tokens(text)
        if est > per_doc_token_cap:
            chars = per_doc_token_cap * 4
            cut = text[:chars]
            if "." in cut:
                cut = cut.rsplit(".", 1)[0] + "."
            text = cut
            est = _estimate_tokens(text)
            hit.doc.text = text
        if total + est > token_budget:
            break
        total += est
        kept.append(hit)
        sources.append({
            "id": hit.doc.meta.get("marker", ""),
            "url": hit.doc.url,
            "title": hit.doc.title,
        })
    return ContextBundle(hits=kept, sources=sources, tokens_est=total)
