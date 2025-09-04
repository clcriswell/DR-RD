"""Utilities for writing run traces atomically.

Temporary files must live on the same filesystem as the destination to keep
``os.replace`` atomic.
"""

import json
import os
import random
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Mapping


def trace_path(run_id: str) -> Path:
    from .paths import run_root

    return run_root(run_id) / "trace.json"


def _read_trace(p: Path) -> list[Any]:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def read_trace(run_id: str) -> list[Any]:
    """Return the saved trace list for ``run_id`` or an empty list."""

    p = trace_path(run_id)
    return _read_trace(p) if p.exists() else []


def _atomic_write(path: Path, text: str) -> None:
    """Atomically write ``text`` to ``path`` using a same-dir temp file.

    The temp file is fsynced before an ``os.replace`` to guarantee durability.
    A small retry loop handles transient races when multiple processes attempt
    to replace the same target.  Temporary files are always unlinked on failure.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{uuid.uuid4().hex}")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        for attempt in range(3):
            try:
                os.replace(tmp, path)
                break
            except (FileNotFoundError, OSError):
                if attempt == 2:
                    raise
                time.sleep(0.05 + random.random() * 0.05)
    finally:
        tmp.unlink(missing_ok=True)


def cleanup_stale_tmp(dir: Path, ttl_sec: int = 3600) -> None:
    """Remove ``*.tmp.*`` files under ``dir`` older than ``ttl_sec`` seconds."""

    now = time.time()
    for p in dir.rglob("*.tmp.*"):
        try:
            if now - p.stat().st_mtime > ttl_sec:
                p.unlink(missing_ok=True)
        except FileNotFoundError:
            continue


_CLEANED = False
_LOCKS: dict[str, Lock] = {}


def _lock_for(run_id: str) -> Lock:
    lock = _LOCKS.get(run_id)
    if lock is None:
        lock = Lock()
        _LOCKS[run_id] = lock
    return lock


def append_step(run_id: str, step: Mapping[str, Any], *, meta: dict | None = None) -> None:
    """Append ``step`` (and optional ``meta``) to the per-run trace.

    The target path is ``.dr_rd/runs/{run_id}/trace.json``.
    """

    global _CLEANED
    if not _CLEANED:
        try:
            from .paths import RUNS_ROOT

            cleanup_stale_tmp(RUNS_ROOT)
        except Exception:  # pragma: no cover - best effort
            pass
        _CLEANED = True

    lock = _lock_for(run_id)
    with lock:
        p = trace_path(run_id)
        data = _read_trace(p) if p.exists() else []
        entry = dict(step)
        if meta is not None:
            entry["meta"] = dict(meta)
        data.append(entry)
        _atomic_write(p, json.dumps(data, ensure_ascii=False))


def append_event(run_id: str, event: Mapping[str, Any]) -> None:
    p = trace_path(run_id)
    data = _read_trace(p) if p.exists() else []
    data.append(dict(event))
    _atomic_write(p, json.dumps(data, ensure_ascii=False))


def flush_phase_meta(run_id: str, phase: str, meta: Mapping[str, Any]) -> None:
    """Optional: write/update a small 'phase_meta.json' for quick UI reads."""

    from .paths import run_root

    root = run_root(run_id)
    p = root / "phase_meta.json"
    try:
        existing = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        existing = {}
    existing[phase] = dict(meta)
    _atomic_write(p, json.dumps(existing, ensure_ascii=False))


__all__ = [
    "trace_path",
    "append_step",
    "append_event",
    "flush_phase_meta",
    "read_trace",
    "cleanup_stale_tmp",
]
