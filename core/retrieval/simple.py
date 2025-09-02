from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - faiss optional
    faiss = None  # type: ignore


def _gather_texts(sources: Iterable[Path]) -> List[tuple[str, str]]:
    items: List[tuple[str, str]] = []
    for path in sources:
        if path.is_file():
            try:
                items.append((path.read_text(encoding="utf-8"), path.as_posix()))
            except Exception:
                continue
    return items


def retrieve(query: str, sources_selected: List[str], top_k: int = 5) -> List[Dict[str, str]]:
    """Return matching docs with citation metadata.

    This is a minimal fallback implementation that avoids heavy dependencies
    when FAISS is unavailable. It performs a naive substring search over
    collected texts from ``samples/`` and ``.dr_rd/uploads/``.
    """
    roots: List[Path] = []
    if "samples" in sources_selected:
        roots.append(Path("samples"))
    if "uploads" in sources_selected:
        roots.append(Path(".dr_rd/uploads"))
    texts: List[tuple[str, str]] = []
    for r in roots:
        texts.extend(_gather_texts(r.rglob("*.txt")))
        texts.extend(_gather_texts(r.rglob("*.md")))
    matches: List[Dict[str, str]] = []
    for text, path in texts:
        if query.lower() in text.lower():
            matches.append({"text": text[:1000], "citation": path})
    return matches[:top_k]
