from __future__ import annotations

"""Utilities for normalising and deduplicating retrieved sources."""

from typing import Dict, List
import hashlib

Source = Dict[str, object]


def _hash_source(src: Source) -> str:
    text = src.get("text") or src.get("snippet") or ""
    url = src.get("url") or ""
    return hashlib.sha256((url + "::" + text).encode("utf-8")).hexdigest()


def merge_and_dedupe(sources: List[Source], similarity_thresh: float = 0.85) -> List[Source]:
    """Merge sources, dropping duplicates based on URL/content hash.

    ``similarity_thresh`` is accepted for API compatibility but unused in this
    lightweight implementation.
    """

    seen: Dict[str, Source] = {}
    deduped: List[Source] = []
    for src in sources:
        h = _hash_source(src)
        if h in seen:
            continue
        seen[h] = src
        if "source_id" not in src:
            src["source_id"] = f"S{len(deduped) + 1}"
        deduped.append(src)
    return deduped


__all__ = ["merge_and_dedupe", "Source"]
