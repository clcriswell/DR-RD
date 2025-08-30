from utils.report_builder import build_markdown_report
from utils.paths import ensure_run_dirs, run_root


def test_build_markdown_report(tmp_path):
    run_id = "test-run"
    ensure_run_dirs(run_id)
    root = run_root(run_id)
    (root / "trace.json").write_text("[]", encoding="utf-8")
    meta = {
        "run_id": run_id,
        "idea_preview": "test idea",
        "mode": "test",
        "started_at": 0,
        "completed_at": 1,
    }
    trace = [
        {
            "phase": "plan",
            "name": "step1",
            "status": "complete",
            "summary": "did thing",
            "duration_ms": 10,
            "tokens": 5,
            "cost": 0.1,
        },
        {"phase": "exec", "name": "step2", "status": "error", "summary": "fail"},
    ]
    totals = {"tokens": 5, "cost": 0.1}
    md = build_markdown_report(run_id, meta, trace, None, totals)
    assert f"DR-RD Report — {run_id}" in md
    assert "## Overview" in md
    assert "Trace summary table" in md
    assert "trace.json" in md
