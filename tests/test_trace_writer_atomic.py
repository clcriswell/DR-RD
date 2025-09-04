import json
from pathlib import Path
from utils import trace_writer


def test_atomic_write_creates_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = ""
    step = {"event": "start"}
    trace_writer.append_step(run_id, step)
    p = trace_writer.trace_path(run_id)
    assert p == Path(".dr_rd") / "runs" / "trace.json"
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data == [step]
