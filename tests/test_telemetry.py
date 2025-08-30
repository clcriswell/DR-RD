import json
from importlib import reload


def test_log_event_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(tmp_path))
    import utils.telemetry as telemetry
    reload(telemetry)
    telemetry.log_event({"event": "sample"})
    assert telemetry.LOG_PATH.exists()
    lines = telemetry.LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event"] == "sample"
    assert "ts" in data
