import json
import zipfile
from pathlib import Path

from core.trace_models import RunMeta, Span
from dr_rd.incidents.bundle import make_incident_bundle


def _write_run(tmp: Path, run_id: str) -> Path:
    run_dir = tmp / run_id
    run_dir.mkdir()
    meta = RunMeta(run_id=run_id, started_at="now", flags={}, budgets={}, models={})
    (run_dir / "run_meta.json").write_text(json.dumps(meta.__dict__))
    span = Span(id="1", parent_id=None, agent="a", tool="t", event=None, meta={}, t_start=0.0, t_end=0.1, duration_ms=100, ok=True)
    (run_dir / "provenance.jsonl").write_text(json.dumps(span.__dict__) + "\n")
    return run_dir


def test_incident_bundle(tmp_path: Path):
    base = _write_run(tmp_path, "base")
    cand = _write_run(tmp_path, "cand")
    out = tmp_path / "out"
    zip_path = make_incident_bundle(base, cand, out)
    assert Path(zip_path).exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        assert "base_run_meta.json" in names
        assert "cand_run_meta.json" in names
        assert "trace_diff.json" in names
        assert "README.md" in names
