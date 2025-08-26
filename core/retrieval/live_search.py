from __future__ import annotations

"""Simplified live search wrapper used by the LangGraph retrieval node.

The real project supports OpenAI and SerpAPI backends with summarisation and
cost tracking.  For the purposes of unit tests we provide a deterministic stub
that respects the :class:`RetrievalBudget` cap and returns mock ``Source``
entries derived from the query strings.
"""

from typing import Dict, List
import datetime as _dt
import uuid

from config import feature_flags as ff
from .budget import RETRIEVAL_BUDGET


Source = Dict[str, object]


def live_search(queries: List[str], caps: Dict[str, int] | None = None) -> List[Source]:
    """Return mock ``Source`` entries for ``queries``.

    Parameters
    ----------
    queries:
        List of query strings.
    caps:
        Ignored in this lightweight implementation; present for API
        compatibility with the real system.
    """

    if not ff.ENABLE_LIVE_SEARCH or not queries:
        return []
    sources: List[Source] = []
    budget = RETRIEVAL_BUDGET
    for q in queries:
        if budget and not budget.allow():
            break
        if budget:
            budget.consume()
        sources.append(
            {
                "source_id": f"L{len(sources) + 1}",
                "url": f"https://example.com/{uuid.uuid4().hex[:8]}",
                "title": q.title(),
                "snippet": q,
                "text": q,
                "tokens": 0,
                "cost": 0.0,
                "when": _dt.datetime.utcnow().isoformat(),
            }
        )
    return sources


__all__ = ["live_search", "Source"]
