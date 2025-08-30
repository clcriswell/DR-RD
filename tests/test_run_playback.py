import csv
from utils.run_playback import (
    load_demo_meta,
    load_demo_trace,
    load_demo_summary,
    materialize_run,
)
import utils.paths as paths


def test_load_demo_meta():
    meta = load_demo_meta()
    assert meta["mode"] == "demo"
    assert "env" in meta


def test_load_demo_trace():
    trace = load_demo_trace()
    assert isinstance(trace, list) and trace
    assert trace[0]["phase"] == "plan"


def test_load_demo_summary():
    report, csv_bytes = load_demo_summary()
    assert "Demo Report" in report
    rows = list(csv.reader(csv_bytes.decode().splitlines()))
    assert len(rows) > 1


def test_materialize_run(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_ROOT", tmp_path)
    run_id = "demo123"
    out = materialize_run(run_id)
    root = tmp_path / run_id
    assert (root / "trace.json").exists()
    assert (root / "summary.csv").exists()
    assert (root / "report.md").exists()
    assert out["trace"]
    assert out["report_md"]
    assert out["totals"]["steps"] == len(out["trace"])
