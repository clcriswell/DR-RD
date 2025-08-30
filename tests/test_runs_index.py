import json
from pathlib import Path

from utils import runs_index


def _write_run(root: Path, run_id: str, *, started: int, status: str, mode: str) -> None:
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "run_id": run_id,
        "started_at": started,
        "completed_at": started + 5,
        "status": status,
        "mode": mode,
        "idea_preview": f"idea {run_id}",
    }
    (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
    totals = {"tokens": 50, "cost_usd": 0.5}
    (run_dir / "usage_totals.json").write_text(json.dumps(totals), encoding="utf-8")


def test_scan_search_csv(tmp_path):
    _write_run(tmp_path, "r1", started=100, status="success", mode="a")
    _write_run(tmp_path, "r2", started=200, status="error", mode="b")
    _write_run(tmp_path, "r3", started=300, status="success", mode="a")
    rows = runs_index.scan_runs(tmp_path)
    assert len(rows) == 3
    succ = runs_index.search(rows, status=["success"])
    assert len(succ) == 2
    date_filtered = runs_index.search(rows, date_from=150, date_to=350)
    assert {r["run_id"] for r in date_filtered} == {"r2", "r3"}
    csv_bytes = runs_index.to_csv(succ)
    text = csv_bytes.decode("utf-8").splitlines()
    assert text[0].startswith("run_id")
    run_ids = {line.split(",")[0] for line in text[1:]}
    assert run_ids == {"r1", "r3"}
