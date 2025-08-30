import sqlite3

from utils.rag import index, textsplit, search

def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "ROOT", tmp_path)
    monkeypatch.setattr(index, "DB", tmp_path / "test.sqlite")
    index.init()


def test_upsert_and_search(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    text = "hello world\nthis is a test"
    chunks = textsplit.split(text, size=10, overlap=0)
    index.upsert_document("doc1", {"name": "d1", "tags": [], "path": ""}, chunks)
    with index._conn() as c:
        docs = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        ch = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        fts = c.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    assert docs == 1
    assert ch == len(chunks)
    assert fts == len(chunks)
    res = search.keyword_search("hello")
    assert res and res[0]["chunk_id"] == "doc1:0"
