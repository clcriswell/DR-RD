import json

from utils import paths, trace_writer


def test_trace_writer_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_ROOT", tmp_path / ".dr_rd" / "runs")
    run_id = "r1"
    trace_writer.append_step(run_id, {"event": "x"})
    p = paths.RUNS_ROOT / run_id / "trace.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert data and data[0]["event"] == "x"
