import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from utils import trace_writer
from utils.paths import ensure_run_dirs


def test_single_writer_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = "run1"
    ensure_run_dirs(run_id)
    trace_writer.append_step(run_id, {"event": "start"})
    p = trace_writer.trace_path(run_id)
    assert p.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == [{"event": "start"}]


def test_concurrent_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = "run2"
    ensure_run_dirs(run_id)

    def worker(i: int) -> None:
        trace_writer.append_step(run_id, {"i": i})

    with ThreadPoolExecutor(max_workers=20) as ex:
        list(ex.map(worker, range(20)))

    p = trace_writer.trace_path(run_id)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data) == 20


def test_cleanup_stale_tmp(tmp_path):
    run_root = tmp_path / ".dr_rd" / "runs"
    run_root.mkdir(parents=True)
    stale = run_root / "trace.json.tmp.dead"
    stale.write_text("x", encoding="utf-8")
    old = time.time() - 7200
    os.utime(stale, (old, old))
    trace_writer.cleanup_stale_tmp(run_root, ttl_sec=1)
    assert not stale.exists()

