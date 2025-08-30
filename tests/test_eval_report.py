from utils.eval import report


def test_report_outputs(tmp_path):
    rows = [
        {
            "id": "t1",
            "tags": ["a"],
            "status": "success",
            "heuristic": 1.0,
            "llm": None,
            "final": 1.0,
            "tokens": 2,
            "cost_usd": 0.01,
            "duration_s": 0.5,
            "run_id": "r1",
        }
    ]
    summary = report.write_scoreboard(tmp_path, rows)
    csv_path = tmp_path / "scoreboard.csv"
    md_path = tmp_path / "scoreboard.md"
    assert csv_path.exists() and md_path.exists()
    txt = md_path.read_text(encoding="utf-8")
    assert "Mean final" in txt and "Pass rate" in txt
    assert summary["pass_rate"] == 1.0
