import json
from pathlib import Path

from scripts.privacy_export import export_run


def test_privacy_export(tmp_path, monkeypatch):
    run_id = "r1"
    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "note.txt").write_text("hello")

    tele_dir = Path(".dr_rd/telemetry")
    tele_dir.mkdir(parents=True, exist_ok=True)
    event = {"event": "test", "run_id": run_id, "msg": "email foo@example.com"}
    (tele_dir / "events-20250101.jsonl").write_text(json.dumps(event) + "\n")

    out = tmp_path / "out"
    summary = export_run(run_id, out)
    assert (out / "runs" / run_id / "note.txt").exists()
    data = (out / "telemetry.jsonl").read_text()
    assert "foo@example.com" not in data
    assert summary["events"] == 1
