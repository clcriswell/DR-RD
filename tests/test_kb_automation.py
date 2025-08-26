from core.retrieval import kb


def test_kb_add_summarize(monkeypatch):
    called = {}

    def fake_update(notes):
        called["notes"] = notes

    monkeypatch.setattr(kb, "update_faiss_index", fake_update)

    src = {"url": "u1", "text": "hello", "title": "t"}
    added = kb.add_sources_to_kb([src])
    assert len(added) == 1
    again = kb.add_sources_to_kb([src])
    assert len(again) == 0

    note = kb.summarize_and_store(src)
    kb.update_faiss_index([note])
    assert called["notes"][0]["id"] == note["id"]
