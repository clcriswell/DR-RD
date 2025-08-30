import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(tmp_path))
    import utils.telemetry as telem
    importlib.reload(telem)
    # yesterday file
    yday = datetime.utcnow() - timedelta(days=1)
    yfile = tmp_path / f"events-{yday.strftime('%Y%m%d')}.jsonl"
    yfile.write_text(json.dumps({"event": "old", "run_id": "old"}) + "\n")
    # today event
    telem.log_event({"event": "run_completed", "run_id": "r1", "status": "success"})
    return telem, yfile


def test_purge(tmp_path, monkeypatch):
    telem, yfile = _setup(tmp_path, monkeypatch)
    tfile = max(telem.list_files())
    # purge older than 0 days -> remove yesterday
    subprocess.check_call(
        [sys.executable, "scripts/telemetry_purge.py", "--older-than", "0"],
        env={**os.environ, "TELEMETRY_LOG_DIR": str(tmp_path)},
    )
    assert not yfile.exists()
    assert tfile.exists()
    # delete run r1
    subprocess.check_call(
        [sys.executable, "scripts/telemetry_purge.py", "--delete-run", "r1"],
        env={**os.environ, "TELEMETRY_LOG_DIR": str(tmp_path)},
    )
    text = tfile.read_text()
    assert "r1" not in text
