import importlib
from pathlib import Path


def test_rotation(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("TELEMETRY_MAX_BYTES", "200")
    import utils.telemetry as telem
    importlib.reload(telem)
    for i in range(50):
        telem.log_event({"event": "test", "i": i})
    files = telem.list_files()
    assert len(files) > 1
    events = telem.read_events()
    assert len(events) == 50
