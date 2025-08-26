from core.retrieval import normalize, rag, live_search


def test_merge_dedupe_and_ids(monkeypatch):
    rag_results = [{"url": "u1", "text": "a", "source_id": "R1"}]
    live_results = [{"url": "u1", "text": "a", "source_id": "L1"}, {"url": "u2", "text": "b"}]

    monkeypatch.setattr(rag, "rag_search", lambda q, k: rag_results)
    monkeypatch.setattr(live_search, "live_search", lambda q, caps: live_results)

    sources = rag.rag_search(["q"], 5) + live_search.live_search(["q"], {})
    merged = normalize.merge_and_dedupe(sources)
    assert len(merged) == 2
    assert merged[0]["source_id"] == "R1"
    assert merged[0]["source_id"] != merged[1]["source_id"]
