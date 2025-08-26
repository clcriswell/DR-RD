from __future__ import annotations

"""Lightweight knowledge-base helpers used by the UI."""

from typing import Dict, List
import hashlib

Source = Dict[str, object]
CanonicalNote = Dict[str, object]

_KB: Dict[str, CanonicalNote] = {}


def _hash_source(src: Source) -> str:
    text = src.get("text") or src.get("snippet") or ""
    url = src.get("url") or ""
    return hashlib.sha256((url + "::" + text).encode("utf-8")).hexdigest()


def add_sources_to_kb(sources: List[Source]) -> Dict[str, CanonicalNote]:
    """Add ``sources`` to the in-memory KB, deduping by hash."""

    added: Dict[str, CanonicalNote] = {}
    for src in sources:
        h = _hash_source(src)
        if h in _KB:
            continue
        note = {"id": h, "title": src.get("title"), "url": src.get("url"), "text": src.get("text")}
        _KB[h] = note
        added[h] = note
    return added


def summarize_and_store(source: Source) -> CanonicalNote:
    """Create a short summary for ``source`` and store it."""

    h = _hash_source(source)
    note = {
        "id": h,
        "title": source.get("title") or source.get("url"),
        "summary": (source.get("text") or "")[:200],
        "url": source.get("url"),
    }
    _KB[h] = note
    return note


def update_faiss_index(notes: List[CanonicalNote]) -> None:
    """Placeholder for FAISS index updates."""

    # Real implementation would chunk ``notes`` and write vectors to the index.
    _ = notes  # no-op


__all__ = [
    "add_sources_to_kb",
    "summarize_and_store",
    "update_faiss_index",
    "Source",
    "CanonicalNote",
]
