import csv
from core.final.traceability import build_rows


def test_traceability_rows(tmp_path):
    intake = {"idea": "Test idea", "constraints": ["one"]}
    tasks = [{"role": "Researcher", "title": "Task A"}]
    routing_report = [{"title": "Task A", "final_role": "Researcher"}]
    answers = {"Researcher": "answer"}
    artifacts = {"evidence": "evidence.json"}

    rows = build_rows("proj", intake, tasks, routing_report, answers, artifacts)
    assert len(rows) == 1
    fieldnames = list(rows[0].keys())
    out_csv = tmp_path / "trace.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    content = out_csv.read_text().strip().splitlines()
    assert content[0].split(",")[0] == "project_id"
    assert len(content) > 1
