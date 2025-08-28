"""Citation bundling utilities."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .types import Hit


def bundle_citations(hits: List[Hit]) -> Tuple[List[Hit], List[Dict[str, str]], Dict[str, str]]:
    sources: List[Dict[str, str]] = []
    marker_map: Dict[str, str] = {}
    next_id = 1
    for hit in hits:
        url = hit.doc.url
        if url not in marker_map:
            marker = f"S{next_id}"
            marker_map[url] = marker
            sources.append({"id": marker, "url": url, "title": hit.doc.title})
            next_id += 1
        hit.doc.meta["marker"] = marker_map[url]
    return hits, sources, marker_map
