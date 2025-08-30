from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, time, uuid, json, fcntl  # use fcntl on posix; fall back to best-effort on win

LOCK_DIR = Path(".dr_rd/locks"); LOCK_DIR.mkdir(parents=True, exist_ok=True)
LOCK_TTL_SEC = 2 * 60 * 60  # 2h

@dataclass(frozen=True)
class RunLock:
    run_id: str
    token: str  # debounce token per submission
    path: Path

def _lock_path(run_id: str) -> Path:
    return LOCK_DIR / f"{run_id}.lock"

def new_token() -> str:
    return uuid.uuid4().hex[:12]

def acquire(run_id: str, token: str) -> RunLock:
    """Create/refresh a lock file for this run_id and write metadata. Return RunLock. Idempotent."""
    p = _lock_path(run_id)
    meta = {"run_id": run_id, "token": token, "ts": time.time()}
    with p.open("w", encoding="utf-8") as f:
        try:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception:
                pass  # best-effort on non-posix
            f.write(json.dumps(meta))
        finally:
            try:
                f.flush()
                os.fsync(f.fileno())
            except Exception:
                pass
    return RunLock(run_id, token, p)

def is_locked(run_id: str) -> bool:
    p = _lock_path(run_id)
    if not p.exists(): return False
    try:
        meta = json.loads(p.read_text(encoding="utf-8") or "{}")
        stale = (time.time() - float(meta.get("ts", 0))) > LOCK_TTL_SEC
        return not stale
    except Exception:
        return True

def release(run_id: str) -> None:
    try: _lock_path(run_id).unlink(missing_ok=True)
    except Exception: pass

def mark_heartbeat(run_id: str) -> None:
    """Update ts to keep the lock fresh during long runs."""
    p = _lock_path(run_id)
    if p.exists():
        try:
            meta = json.loads(p.read_text(encoding="utf-8") or "{}")
            meta["ts"] = time.time()
            p.write_text(json.dumps(meta), encoding="utf-8")
        except Exception:
            pass
