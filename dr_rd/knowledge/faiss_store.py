from __future__ import annotations

import os
from typing import List, Tuple, Optional

try:  # pragma: no cover - numpy may be missing
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - faiss may be missing
    import faiss
except Exception:  # pragma: no cover
    faiss = None  # type: ignore

from dr_rd.knowledge.retriever import Retriever


def _embed(text: str, dim: int = 128) -> np.ndarray:
    """Very simple hashing-based embedding for offline usage."""
    if np is None:
        return []  # type: ignore
    vec = np.zeros(dim, dtype="float32")
    for i, token in enumerate(text.split()):
        vec[i % dim] += (hash(token) % 1000) / 1000.0
    return vec


class FaissStore(Retriever):
    """Minimal FAISS-backed store using local embeddings."""

    def __init__(self, texts: List[str], sources: List[str]):
        if faiss is None or np is None:
            raise ImportError("faiss and numpy are required for FaissStore")
        self.texts = texts
        self.sources = sources
        embeddings = np.vstack([_embed(t) for t in texts])
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def query(self, text: str, top_k: int) -> List[Tuple[str, str]]:
        if faiss is None or np is None:
            return []
        vec = _embed(text)
        D, I = self.index.search(np.expand_dims(vec, 0), top_k)
        results: List[Tuple[str, str]] = []
        for idx in I[0]:
            if idx < len(self.texts):
                results.append((self.texts[idx], self.sources[idx]))
        return results


def build_default_retriever() -> Optional[Retriever]:
    """Build a store over local README as a best-effort corpus."""
    if faiss is None or np is None:
        return None
    root = os.getcwd()
    docs: List[str] = []
    sources: List[str] = []
    readme = os.path.join(root, "README.md")
    if os.path.exists(readme):
        with open(readme, "r", encoding="utf-8") as f:
            docs.append(f.read())
            sources.append("README.md")
    if not docs:
        return None
    return FaissStore(docs, sources)
