import json
import time
from pathlib import Path

from utils import metrics


def test_load_events_trims_and_caches(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for i in range(50):
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"idx": i, "event": "e", "ts": i}) + "\n")
    monkeypatch.setattr(metrics, "EVENTS_PATH", path)
    metrics.load_events.clear()
    calls = {"n": 0}

    orig_open = Path.open

    def counting_open(self, *args, **kwargs):
        if self == path:
            calls["n"] += 1
        return orig_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counting_open)

    first = metrics.load_events(limit=10)
    assert len(first) == 10
    assert first[0]["idx"] == 40
    second = metrics.load_events(limit=10)
    assert len(second) == 10
    assert calls["n"] == 1


def test_compute_aggregates():
    now = time.time()
    events = [
        {"event": "start_run", "ts": now},
        {"event": "run_complete", "success": True, "duration_s": 4, "ts": now + 4},
        {"event": "start_run", "ts": now + 10},
        {"event": "run_complete", "success": False, "duration_s": 6, "ts": now + 16},
        {"event": "error_shown", "ts": now + 17},
        {"event": "nav_page_view", "ts": now},
    ]
    surveys = [
        {"instrument": "SUS", "total": 80, "ts": now},
        {"instrument": "SUS", "total": 60, "ts": now},
        {"instrument": "SEQ", "answers": {"score": 3}, "ts": now},
        {"instrument": "SEQ", "answers": {"score": 5}, "ts": now},
    ]
    agg = metrics.compute_aggregates(events, surveys)
    assert agg["runs"] == 2
    assert agg["views"] == 1
    assert agg["errors"] == 1
    assert agg["error_rate"] == 0.5
    assert agg["success_rate"] == 0.5
    assert agg["avg_time_on_task"] == 5
    assert agg["sus_count"] == 2
    assert agg["sus_mean"] == 70
    assert agg["seq_7_day_mean"] == 4


def test_list_artifacts(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    monkeypatch.setattr(metrics, "ARTIFACTS_DIR", tmp_path)
    metrics.list_artifacts.clear()
    mapping = metrics.list_artifacts()
    assert mapping == {"a.txt": str(tmp_path / "a.txt"), "b.txt": str(tmp_path / "b.txt")}
