import csv
import os
import subprocess
import sys

import pytest


def _write_events(tmp_path, monkeypatch):
    import importlib
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(tmp_path))
    import utils.telemetry as telem
    importlib.reload(telem)
    telem.log_event({"event": "start_run", "run_id": "r1"})
    telem.log_event({"event": "error_shown", "run_id": "r1"})
    telem.log_event({"event": "run_completed", "run_id": "r1", "status": "success"})
    return telem


def test_export_csv(tmp_path, monkeypatch):
    _write_events(tmp_path, monkeypatch)
    out = tmp_path / "events.csv"
    subprocess.check_call(
        [sys.executable, "scripts/telemetry_export.py", "--days", "1", "--out", str(out)],
        env={**os.environ, "TELEMETRY_LOG_DIR": str(tmp_path)},
    )
    import csv
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 3
    assert "event" in rows[0]


@pytest.mark.skipif(not pytest.importorskip("pyarrow", reason="pyarrow not installed"), reason="pyarrow not installed")
def test_export_parquet(tmp_path, monkeypatch):
    _write_events(tmp_path, monkeypatch)
    out = tmp_path / "events.parquet"
    subprocess.check_call(
        [sys.executable, "scripts/telemetry_export.py", "--days", "1", "--out", str(out)],
        env={**os.environ, "TELEMETRY_LOG_DIR": str(tmp_path)},
    )
    import pyarrow.parquet as pq

    table = pq.read_table(out)
    assert table.num_rows >= 3
