"""Basic retriever interfaces."""

from __future__ import annotations

import abc
from typing import List

from .types import Doc, QuerySpec


class Retriever(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def search(self, spec: QuerySpec) -> List[Doc]:
        """Return ``Doc`` objects matching ``spec``.

        Implementations may attach a raw score in ``doc.meta['score']``.
        """


class BM25LiteRetriever(Retriever):
    """Very small TF-IDF/BM25 style retriever using in-memory docs."""

    name = "bm25"

    def __init__(self, docs: List[Doc]):
        self.docs = docs

    def search(self, spec: QuerySpec) -> List[Doc]:
        terms = spec.query.lower().split()
        scored: List[Doc] = []
        for doc in self.docs:
            text = doc.text.lower()
            score = sum(text.count(t) for t in terms)
            d = Doc(**doc.__dict__)
            d.meta["score"] = float(score)
            scored.append(d)
        scored.sort(key=lambda d: d.meta.get("score", 0.0), reverse=True)
        return scored[: spec.top_k]


class DenseRetriever(Retriever):
    """Stub dense retriever that falls back if embeddings unavailable."""

    name = "dense"

    def __init__(self, docs: List[Doc], embed_fn=None):
        self.docs = docs
        self.embed_fn = embed_fn

    def search(self, spec: QuerySpec) -> List[Doc]:
        if not self.embed_fn:
            return []
        q_emb = self.embed_fn(spec.query)
        scored: List[Doc] = []
        for doc in self.docs:
            d_emb = self.embed_fn(doc.text)
            score = sum(q_emb.get(k, 0) * d_emb.get(k, 0) for k in q_emb)
            d = Doc(**doc.__dict__)
            d.meta["score"] = float(score)
            scored.append(d)
        scored.sort(key=lambda d: d.meta.get("score", 0.0), reverse=True)
        return scored[: spec.top_k]


class WebSearchRetriever(Retriever):
    name = "web"

    def __init__(self, search_fn):
        self.search_fn = search_fn

    def search(self, spec: QuerySpec) -> List[Doc]:
        return self.search_fn(spec.query, spec.top_k)


class KBRetriever(Retriever):
    name = "kb"

    def __init__(self, kb_docs: List[Doc]):
        self.docs = kb_docs

    def search(self, spec: QuerySpec) -> List[Doc]:
        return self.docs[: spec.top_k]
