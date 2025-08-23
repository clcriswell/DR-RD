from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Protocol


class FAISSLoadError(Exception):
    """Raised when a FAISS index cannot be loaded."""


@dataclass
class Snippet:
    text: str
    source: str


class Retriever(Protocol):
    def query(self, text: str, top_k: int) -> List[Snippet]: ...


class _NullRetriever:
    def query(self, text: str, top_k: int) -> List[Snippet]:
        return []


def build_default_retriever(path: str | None = None) -> Tuple[Retriever, int, int]:
    """Return a FAISS retriever, document count, and embedding dims.

    Parameters
    ----------
    path:
        Directory containing ``index.faiss`` and ``docs.json``.  When omitted
        ``.faiss_index`` is used.

    Returns
    -------
    (retriever, doc_count, dims)

    Raises
    ------
    FAISSLoadError
        If the bundle is missing or invalid.
    """

    p = Path(path or ".faiss_index")
    index_file = p / "index.faiss"
    meta_file = p / "docs.json"
    if not index_file.exists() or not meta_file.exists():
        raise FAISSLoadError("missing index or metadata")
    try:
        import json
        import faiss  # type: ignore
    except Exception as e:  # pragma: no cover - optional dep
        raise FAISSLoadError(str(e)) from e
    try:
        index = faiss.read_index(str(index_file))
        dims = index.d
        with open(meta_file, "r", encoding="utf-8") as fh:
            docs = json.load(fh) or []
    except Exception as e:  # pragma: no cover
        raise FAISSLoadError(str(e)) from e

    doc_count = len(docs)

    class _FaissRetriever:
        def __init__(self, idx, docs):
            self.index = idx
            self.docs = docs

        def query(self, text: str, top_k: int) -> List[Snippet]:  # pragma: no cover - simple stub
            # This stub returns no results; actual similarity search is out of scope
            return []

    return _FaissRetriever(index, docs), doc_count, dims
