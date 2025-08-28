from __future__ import annotations

import re
import urllib.parse
from typing import Dict, Iterable, List, Tuple

from dataclasses import asdict

from dr_rd.kb.models import KBSource


def _canonical_url(url: str | None) -> str:
    if not url:
        return ""
    parts = urllib.parse.urlparse(url)
    scheme = parts.scheme or "http"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urllib.parse.urlunparse((scheme, netloc, path, "", "", ""))


def normalize_sources(sources: List[Dict]) -> List[KBSource]:
    seen: Dict[Tuple[str, str], KBSource] = {}
    for s in sources or []:
        src = KBSource(**s)
        key = (_canonical_url(src.url), (src.title or "").strip())
        if key not in seen:
            seen[key] = src
    return list(seen.values())


def merge_agent_sources(*source_lists: Iterable[KBSource]) -> List[KBSource]:
    merged: Dict[Tuple[str, str], KBSource] = {}
    for lst in source_lists:
        for s in lst or []:
            key = (_canonical_url(s.url), (s.title or "").strip())
            if key not in merged:
                merged[key] = s
    return list(merged.values())


def bundle_citations(sections: List[Tuple[str, List[KBSource]]]):
    """Assign stable citation markers across ``sections``.

    Each item in ``sections`` is a tuple ``(text, sources)`` where ``text`` may
    contain placeholders ``{{source_id}}`` referencing the ``id`` field of items
    in ``sources``.
    Returns a list of processed section texts and the final de-duplicated source
    list in marker order.
    """

    processed: List[str] = []
    order: Dict[Tuple[str, str], int] = {}
    final_sources: List[KBSource] = []
    for text, sources in sections:
        sources = normalize_sources([asdict(s) if not isinstance(s, dict) else s for s in sources])
        for src in sources:
            key = (_canonical_url(src.url), (src.title or "").strip())
            if key not in order:
                order[key] = len(order) + 1
                final_sources.append(src)
            marker = f"S{order[key]}"
            text = text.replace(f"{{{{{src.id}}}}}", f"[{marker}]")
        processed.append(text)
    return processed, final_sources
