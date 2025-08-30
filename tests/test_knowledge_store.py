from pathlib import Path
from utils import knowledge_store


def setup_store(monkeypatch, tmp_path):
    root = tmp_path / "store"
    monkeypatch.setattr(knowledge_store, "ROOT", root)
    monkeypatch.setattr(knowledge_store, "UPLOADS", root / "uploads")
    monkeypatch.setattr(knowledge_store, "META", root / "meta.json")
    knowledge_store.init_store()


def test_roundtrip(monkeypatch, tmp_path):
    setup_store(monkeypatch, tmp_path)
    tmp_file = knowledge_store.UPLOADS / "a.txt"
    tmp_file.write_text("hi", encoding="utf-8")
    item = knowledge_store.add_item("a.txt", tmp_file, tags=["foo"], kind="upload")
    meta_tmp = knowledge_store.META.with_name("meta.json.tmp")
    assert not meta_tmp.exists()
    assert Path(item["path"]).parent == knowledge_store.UPLOADS
    assert knowledge_store.get_item(item["id"]) is not None
    assert knowledge_store.list_items(["foo"])
    updated = knowledge_store.set_tags(item["id"], ["bar"])
    assert updated["tags"] == ["bar"]
    assert knowledge_store.list_items(["bar"])
    assert not meta_tmp.exists()
    assert knowledge_store.remove_item(item["id"])
    assert knowledge_store.list_items() == []
    assert not tmp_file.exists()
    assert not meta_tmp.exists()
