from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(".dr_rd/index")
ROOT.mkdir(parents=True, exist_ok=True)
DB = ROOT / "knowledge.sqlite"

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, name TEXT, tags TEXT, item_path TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, doc_id TEXT, ord INTEGER, text TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content='chunks', content_rowid='rowid');
CREATE TABLE IF NOT EXISTS embeddings (chunk_id TEXT PRIMARY KEY, vec TEXT);
"""


def _conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init() -> None:
    c = _conn()
    for stmt in filter(None, DDL.split(";")):
        s = stmt.strip()
        if s:
            c.execute(s)
    c.commit()
    c.close()


def upsert_document(doc_id: str, meta: Dict[str, Any], chunks: Iterable[str], *, embedder=None) -> int:
    """
    meta: {'name':..., 'tags': [...], 'path': ...}
    embedder: callable(list[str]) -> list[list[float]] | None
    """
    init()
    chunks = list(chunks)
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO documents(id,name,tags,item_path,created_at) VALUES(?,?,?,?,?)",
            (doc_id, meta.get("name", ""), json.dumps(meta.get("tags", [])), meta.get("path", ""), now),
        )
        # remove existing chunks and fts entries
        c.execute(
            "DELETE FROM chunks_fts WHERE rowid IN (SELECT rowid FROM chunks WHERE doc_id=?)",
            (doc_id,),
        )
        c.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
        # remove old embeddings
        c.execute("DELETE FROM embeddings WHERE chunk_id LIKE ?", (f"{doc_id}:%",))
        # insert chunks
        for i, t in enumerate(chunks):
            cid = f"{doc_id}:{i}"
            cur = c.execute(
                "INSERT OR REPLACE INTO chunks(id,doc_id,ord,text) VALUES(?,?,?,?)",
                (cid, doc_id, i, t),
            )
            rowid = cur.lastrowid
            c.execute("INSERT INTO chunks_fts(rowid, text) VALUES(?, ?)", (rowid, t))
        # embeddings
        if embedder:
            vecs = embedder(chunks) or []
            if vecs:
                rows = [(f"{doc_id}:{i}", json.dumps(vec)) for i, vec in enumerate(vecs)]
                c.executemany(
                    "INSERT OR REPLACE INTO embeddings(chunk_id, vec) VALUES(?, ?)",
                    rows,
                )
    return len(chunks)
