from __future__ import annotations

from typing import Dict, List, Tuple
from urllib.parse import urlparse

from .schemas import Citation, CitationKind


def build_citation_graph(claims: List[Dict], sources: List[Dict]) -> Tuple[List[Citation], Dict[str, str]]:
    citations: List[Citation] = []
    mapping: Dict[str, str] = {}
    for idx, src in enumerate(sources, start=1):
        sid = src.get("id") or src.get("url") or str(idx)
        label = f"S{idx}"
        mapping[sid] = label
        domain = urlparse(src.get("url", "")).netloc
        claim_id = claims[min(idx - 1, len(claims) - 1)]["id"] if claims else ""
        citations.append(
            Citation(
                id=label,
                claim_id=claim_id,
                source_id=sid,
                url=src.get("url", ""),
                domain=domain,
                kind=CitationKind.other,
            )
        )
    return citations, mapping


def validate_citations(citations: List[Citation], allow_domains: List[str], min_coverage: float) -> Dict:
    claims = {c.claim_id for c in citations}
    covered = {c.claim_id for c in citations if c.domain in allow_domains}
    total = len(claims) or 1
    coverage = len(covered) / total
    missing = list(claims - covered)
    return {"coverage": coverage, "missing": missing, "ok": coverage >= min_coverage}
