import os
from dr_rd.privacy import subject


def test_subject_key_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVACY_SALT", "salt1")
    record = {"email": "a@example.com"}
    key1 = subject.derive_subject_key(record, ["email"], "PRIVACY_SALT")
    key2 = subject.derive_subject_key(record, ["email"], "PRIVACY_SALT")
    assert key1 == key2
    monkeypatch.setenv("PRIVACY_SALT", "salt2")
    key3 = subject.derive_subject_key(record, ["email"], "PRIVACY_SALT")
    assert key1 != key3
