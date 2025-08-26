from __future__ import annotations

"""Heuristic query construction for retrieval pipelines.

The real implementation would apply keyword expansion and more sophisticated
logic.  For the purposes of the tests we implement a lightweight splitter that
produces unique, length-bounded search queries derived from the task and
project context.
"""

from typing import Iterable, List

MAX_QUERY_LEN = 64
MAX_QUERIES_PER_TASK = 8


def build_queries(
    task: str,
    idea: str,
    constraints: Iterable[str] | None = None,
    risk_posture: str | None = None,
    *,
    max_queries: int = MAX_QUERIES_PER_TASK,
    max_len: int = MAX_QUERY_LEN,
) -> List[str]:
    """Return a list of normalized query strings.

    Parameters
    ----------
    task, idea, constraints, risk_posture:
        High level description of the current task.  Only ``task`` and ``idea``
        materially influence the output in this simplified implementation.
    max_queries:
        Maximum number of queries to emit.
    max_len:
        Maximum characters per query.
    """

    parts: List[str] = [task or "", idea or ""]
    if constraints:
        parts.extend([c or "" for c in constraints])
    text = " ".join(parts)

    queries: List[str] = []
    seen = set()
    for token in text.split():
        norm = token.strip()
        if not norm:
            continue
        low = norm.lower()
        if low in seen:
            continue
        seen.add(low)
        queries.append(norm[:max_len])
        if len(queries) >= max_queries:
            break
    return queries

__all__ = ["build_queries", "MAX_QUERY_LEN", "MAX_QUERIES_PER_TASK"]
