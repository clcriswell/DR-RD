from __future__ import annotations

import json
import math
from typing import Any, Dict, List

from .index import _conn


def keyword_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT chunks.id, chunks.doc_id, bm25(chunks_fts) AS score, chunks.text "
            "FROM chunks_fts JOIN chunks ON chunks_fts.rowid = chunks.rowid "
            "WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?",
            (query, limit),
        ).fetchall()
    return [
        {"chunk_id": r[0], "doc_id": r[1], "score": float(r[2]), "text": r[3]} for r in rows
    ]


def embed_search(query_vec: list[float], limit: int = 20) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute("SELECT chunk_id, vec FROM embeddings").fetchall()
    scored = []
    for cid, vec_json in rows:
        v = json.loads(vec_json)
        dot = sum(a * b for a, b in zip(query_vec, v))
        na = math.sqrt(sum(a * a for a in query_vec)) or 1.0
        nb = math.sqrt(sum(b * b for b in v)) or 1.0
        scored.append((cid, dot / (na * nb)))
    scored.sort(key=lambda x: x[1], reverse=True)
    out = []
    with _conn() as c:
        for cid, s in scored[:limit]:
            row = c.execute("SELECT doc_id, text FROM chunks WHERE id=?", (cid,)).fetchone()
            if row:
                out.append(
                    {
                        "chunk_id": cid,
                        "doc_id": row[0],
                        "score": float(s),
                        "text": row[1],
                    }
                )
    return out


def hybrid(query: str, query_vec: list[float] | None, k: int = 4) -> List[Dict[str, Any]]:
    kw = keyword_search(query, limit=max(20, k * 5))
    if query_vec is None:
        return kw[:k]
    emb = embed_search(query_vec, limit=max(20, k * 5))

    def rrf(rank: int) -> float:
        return 1.0 / (50.0 + rank)

    combined: list[tuple[str, float, Dict[str, Any]]] = []
    seen: set[str] = set()
    for L in (kw, emb):
        for r, item in enumerate(L):
            key = item["chunk_id"]
            if key not in seen:
                seen.add(key)
                combined.append((key, rrf(r + 1), item))
            else:
                for j, (k2, score, it2) in enumerate(combined):
                    if k2 == key:
                        combined[j] = (k2, score + rrf(r + 1), it2)
                        break
    combined.sort(key=lambda x: x[1], reverse=True)
    return [it for _, __, it in combined[:k]]
