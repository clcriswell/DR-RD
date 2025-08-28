import json
from pathlib import Path

from core.trace_models import RunMeta, Span
from core import ui_bridge


def _write_run(tmp: Path, run_id: str) -> Path:
    run_dir = tmp / run_id
    run_dir.mkdir()
    meta = RunMeta(run_id=run_id, started_at="now", flags={}, budgets={}, models={})
    (run_dir / "run_meta.json").write_text(json.dumps(meta.__dict__))
    span = Span(id="1", parent_id=None, agent="a", tool="t", event=None, meta={}, t_start=0.0, t_end=0.1, duration_ms=100, ok=True)
    (run_dir / "provenance.jsonl").write_text(json.dumps(span.__dict__) + "\n")
    return run_dir


def test_ui_bridge_trace_ops(tmp_path: Path):
    base = _write_run(tmp_path, "base")
    cand = _write_run(tmp_path, "cand")
    runs = ui_bridge.list_runs(tmp_path)
    assert len(runs) == 2
    meta, spans = ui_bridge.load_run(base)
    assert meta["run_id"] == "base"
    diff = ui_bridge.diff_runs(base, cand)
    assert "spans_added" in diff
    bundle = ui_bridge.make_incident_bundle(base, cand, tmp_path / "out")
    assert Path(bundle).exists()
    summary = ui_bridge.redaction_summary(base)
    assert isinstance(summary, dict)
