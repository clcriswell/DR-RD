from __future__ import annotations

"""Vector search helpers for Retrieval-Augmented Generation (RAG).

The production system uses a FAISS index configured via ``config.feature_flags``.
Here we provide a minimal stub that returns deterministic results suitable for
unit tests.  Callers are expected to patch this function when exercising merge
logic.
"""

from typing import Dict, List

from config import feature_flags as ff

Source = Dict[str, object]


def rag_search(queries: List[str], top_k: int) -> List[Source]:
    """Return mock RAG ``Source`` entries."""

    if not ff.RAG_ENABLED or not queries:
        return []
    results: List[Source] = []
    for i, q in enumerate(queries[: top_k or len(queries)], 1):
        results.append(
            {
                "source_id": f"R{i}",
                "url": f"faiss://{i}",
                "title": q,
                "snippet": q,
                "text": q,
                "tokens": 0,
                "cost": 0.0,
                "when": "",
            }
        )
    return results


__all__ = ["rag_search", "Source"]
