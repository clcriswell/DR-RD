import os
from core.final.composer import write_final_bundle

import dr_rd.reporting.report_builder as rb


def test_final_report_formatting(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    os.chdir(cwd)
    meta = {
        "run_id": "run123",
        "intake": ("Build a quantum device", ["use silicon"], set()),
        "mode": "standard",
        "started_at": 0,
        "completed_at": 1,
    }
    trace = [
        {
            "phase": "executor",
            "name": "Materials Selection for Quantum Components",
            "status": "complete",
            "duration_ms": 10,
            "tokens": 8,
            "cost": 0.02,
            "summary": "done",
        },
        {
            "phase": "synthesizer",
            "name": "Final Synthesis",
            "status": "complete",
            "duration_ms": 5,
            "tokens": 7,
            "cost": 0.03,
            "summary": "final",
        },
    ]
    totals = {"tokens": 15, "cost": 0.05}
    md = rb.build_markdown_report("run123", meta, trace, None, totals)
    assert "Idea: Build a quantum device" in md
    assert "Constraints: use silicon" in md
    assert "executor" in md and "Materials Selection for Quantum Components" in md
    assert "synthesizer" in md and "Final Synthesis" in md
    assert "Tokens: 15" in md
    assert "Cost: $0.0500" in md
    assert "None" not in md
    out = write_final_bundle("run123", md, {}, [])
    assert (cwd / out["report"]).exists()
