import json
from pathlib import Path

from core.trace_models import RunMeta, Span
from core.trace_diff import load_run, diff_runs


def _write_run(tmp: Path, run_id: str, spans: list[Span]) -> Path:
    run_dir = tmp / run_id
    run_dir.mkdir()
    meta = RunMeta(run_id=run_id, started_at="now", flags={}, budgets={}, models={})
    (run_dir / "run_meta.json").write_text(json.dumps(meta.__dict__))
    with (run_dir / "provenance.jsonl").open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s.__dict__) + "\n")
    return run_dir


def test_trace_diff_alignment(tmp_path: Path):
    base_spans = [Span(id="1", parent_id=None, agent="a", tool="t", event=None, meta={}, t_start=0.0, t_end=0.1, duration_ms=100, ok=True)]
    cand_spans = base_spans + [Span(id="2", parent_id=None, agent="a", tool="t", event=None, meta={}, t_start=0.1, t_end=0.2, duration_ms=100, ok=True)]
    base_dir = _write_run(tmp_path, "base", base_spans)
    cand_dir = _write_run(tmp_path, "cand", cand_spans)

    base_run = load_run(base_dir)
    cand_run = load_run(cand_dir)
    diff = diff_runs(base_run, cand_run)

    assert len(diff["spans_added"]) == 1
    assert diff["spans_added"][0]["id"] == "2"
