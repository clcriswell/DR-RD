from __future__ import annotations

import os
import json
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


class _FaissDiskStore(Retriever):
    def __init__(self, index, texts, sources):
        self.index = index
        self.texts = texts
        self.sources = sources

    def query(self, text: str, top_k: int):
        if faiss is None or np is None:
            return []
        vec = _embed(text)  # must match the offline embedder
        D, I = self.index.search(np.array([vec]), min(top_k, len(self.texts)))
        results = []
        for idx in I[0]:
            if 0 <= idx < len(self.texts):
                results.append((self.texts[idx], self.sources[idx]))
        return results


def load_disk_store(root: str = ".", mem_dir: str = "memory") -> Optional[Retriever]:
    if faiss is None or np is None:
        return None
    idx_path = os.path.join(root, mem_dir, "index.faiss")
    meta_path = os.path.join(root, mem_dir, "texts.json")
    if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
        return None
    try:
        index = faiss.read_index(idx_path)
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        return _FaissDiskStore(index, meta.get("texts", []), meta.get("sources", []))
    except Exception:
        return None



def build_default_retriever() -> Optional[Retriever]:
    """Prefer a disk index under ./memory; else fall back to README."""
    if faiss is None or np is None:
        return None
    disk = load_disk_store()
    if disk:
        return disk
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
