from utils.rag import index, search, textsplit


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "ROOT", tmp_path)
    monkeypatch.setattr(index, "DB", tmp_path / "test.sqlite")
    index.init()


def test_hybrid_merges(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    chunks1 = textsplit.split("alpha beta", size=50, overlap=0)
    chunks2 = textsplit.split("beta gamma", size=50, overlap=0)

    def emb1(chs):
        return [[0.0, 1.0] for _ in chs]

    def emb2(chs):
        return [[1.0, 0.0] for _ in chs]

    index.upsert_document("d1", {"name": ""}, chunks1, embedder=emb1)
    index.upsert_document("d2", {"name": ""}, chunks2, embedder=emb2)

    kw = search.keyword_search("alpha")
    assert kw and kw[0]["chunk_id"] == "d1:0"

    res = search.hybrid("alpha", [1.0, 0.0], k=2)
    ids = {r["chunk_id"] for r in res}
    assert {"d1:0", "d2:0"} <= ids
