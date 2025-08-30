import json
from utils.trace_writer import append_step, trace_path, flush_phase_meta
from utils.paths import ensure_run_dirs, run_root


def test_append_and_flush(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = "r1"
    ensure_run_dirs(run_id)
    append_step(run_id, {"id": "s1", "summary": "a"})
    append_step(run_id, {"id": "s2", "summary": "b"})
    data = json.loads(trace_path(run_id).read_text())
    assert [s["summary"] for s in data] == ["a", "b"]

    flush_phase_meta(run_id, "planner", {"duration": 1})
    flush_phase_meta(run_id, "planner", {"duration": 1})
    meta_path = run_root(run_id) / "phase_meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["planner"]["duration"] == 1
