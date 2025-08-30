from utils.report_html import build_html_report


def test_build_html_report():
    run_id = "run1"
    meta = {
        "idea_preview": "<idea & demo>",
        "mode": "test",
        "started_at": 0,
        "completed_at": 1,
    }
    rows = [
        {
            "i": 1,
            "phase": "plan",
            "name": "step1",
            "status": "complete",
            "duration_ms": 10,
            "tokens": 5,
            "cost": 0.1,
            "summary": "did <thing> & stuff",
        },
        {
            "i": 2,
            "phase": "exec",
            "name": "step2",
            "status": "error",
            "duration_ms": 20,
            "tokens": 10,
            "cost": 0.2,
            "summary": "oops <script>alert(1)</script>",
        },
    ]
    totals = {"tokens": 15, "cost": 0.3}
    html = build_html_report(run_id, meta, rows, "summary & <b>", totals, [("file.txt", "file.txt")])

    assert f"DR RD Report — {run_id}" in html
    assert "Tokens" in html and "Cost" in html
    assert "<th>Phase</th>" in html
    assert "&lt;b&gt;" in html  # escaped user text
    assert "<script" not in html.lower()
    assert "@media print" in html
    assert len(html.encode("utf-8")) < 1_000_000
