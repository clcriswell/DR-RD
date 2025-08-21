import os
import uuid
from memory.decision_log import log_decision, _path


def test_log_decision():
    pid = f"proj_{uuid.uuid4().hex}"
    log_decision(pid, "route", {"x": 1})
    p = _path(pid)
    assert os.path.exists(p)
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
