import os
import time

from utils import retention


def test_purge_and_delete(tmp_path, monkeypatch):
    tel = tmp_path / "telemetry"
    runs_dir = tmp_path / "runs"
    tel.mkdir()
    runs_dir.mkdir()
    monkeypatch.setattr(retention, "TEL_DIR", tel)
    monkeypatch.setattr(retention, "RUNS_DIR", runs_dir)

    old_time = time.time() - 10 * 86400

    old_file = tel / "events-old.jsonl"
    old_file.write_text("a\n", encoding="utf-8")
    os.utime(old_file, (old_time, old_time))
    new_file = tel / "events-new.jsonl"
    new_file.write_text("b\n", encoding="utf-8")

    removed = retention.purge_telemetry_older_than(7)
    assert removed == 1
    assert not old_file.exists() and new_file.exists()

    run_old = runs_dir / "r1"
    run_old.mkdir()
    os.utime(run_old, (old_time, old_time))
    run_new = runs_dir / "r2"
    run_new.mkdir()

    removed_runs = retention.purge_runs_older_than(7)
    assert removed_runs == 1
    assert not run_old.exists() and run_new.exists()

    tel_file = tel / "events-123.jsonl"
    tel_file.write_text('{"run_id":"r2"}\n{"run_id":"other"}\n', encoding="utf-8")
    rewritten = retention.delete_run_events("r2")
    assert rewritten == 1
    txt = tel_file.read_text(encoding="utf-8")
    assert "r2" not in txt and "other" in txt

    assert retention.delete_run("r2")
    assert not run_new.exists()
