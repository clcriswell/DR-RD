import json
import time

from utils import session_store


def test_cleanup_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESS_DIR", tmp_path / "sess")
    session_store.SESS_DIR.mkdir(parents=True, exist_ok=True)
    old_json = session_store.SESS_DIR / "old_run.json"
    old_json.write_text(json.dumps({"saved_at": time.time() - 100}))
    old_touch = session_store.SESS_DIR / "old.touch"
    old_touch.write_text(str(time.time() - 100))
    removed = session_store.cleanup_expired(ttl_sec=10)
    assert removed == 2
    assert not old_json.exists()
    assert not old_touch.exists()
