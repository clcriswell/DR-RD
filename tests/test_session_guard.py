from __future__ import annotations

import json
import time

from utils import session_guard


def test_acquire_release(tmp_path):
    run_id = "test_run1"
    token = session_guard.new_token()
    session_guard.acquire(run_id, token)
    assert session_guard.is_locked(run_id)
    session_guard.release(run_id)
    assert not session_guard.is_locked(run_id)


def test_ttl_expiry(tmp_path):
    run_id = "test_run2"
    token = session_guard.new_token()
    lock = session_guard.acquire(run_id, token)
    stale = {"run_id": run_id, "token": token, "ts": time.time() - session_guard.LOCK_TTL_SEC - 10}
    lock.path.write_text(json.dumps(stale), encoding="utf-8")
    assert not session_guard.is_locked(run_id)
    session_guard.release(run_id)


def test_ui_flow_blocking(tmp_path):
    run_id = "test_run3"
    state = {"active_run": None}

    # first submission
    token1 = session_guard.new_token()
    session_guard.acquire(run_id, token1)
    state["active_run"] = {"run_id": run_id, "token": token1, "status": "running"}

    # second submit should be blocked
    blocked = state["active_run"] and state["active_run"]["status"] == "running"
    assert blocked

    session_guard.release(run_id)
    state["active_run"] = None

    # after release, next submit allowed
    blocked = False
    if state.get("active_run") and state["active_run"].get("status") == "running":
        blocked = True
    else:
        token2 = session_guard.new_token()
        session_guard.acquire(run_id, token2)
        state["active_run"] = {"run_id": run_id, "token": token2, "status": "running"}
    assert not blocked
    session_guard.release(run_id)
