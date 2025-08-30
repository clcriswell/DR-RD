from utils import knowledge_store, uploads


def test_sanitize_filename():
    assert uploads.sanitize_filename("a b??.txt") == "a b.txt"
    assert uploads.sanitize_filename("   spaces   ") == "spaces"


def test_allowed_ext():
    assert uploads.allowed_ext("file.TXT")
    assert not uploads.allowed_ext("file.exe")


def test_unique_upload_path(monkeypatch, tmp_path):
    monkeypatch.setattr(knowledge_store, "UPLOADS", tmp_path)
    p1 = uploads.unique_upload_path("doc.txt")
    p2 = uploads.unique_upload_path("doc.txt")
    assert p1.parent == tmp_path
    assert p1 != p2
