import json
from pathlib import Path

from utils import checkpoints


def test_checkpoints_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    checkpoints.ROOT = tmp_path
    cp = checkpoints.init("run1", phases=["planner"])
    checkpoints.mark_step_done("run1", "planner", 1)
    checkpoints.mark_step_done("run1", "planner", 2)
    loaded = checkpoints.load("run1")
    assert loaded["phases"]["planner"]["next_index"] == 2
    assert checkpoints.last_completed_index("run1", "planner") == 2
    # ensure json structure stable
    p = checkpoints.path("run1")
    data = json.loads(p.read_text())
    assert data == loaded
