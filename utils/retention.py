"""Helpers for data retention and deletion."""

from __future__ import annotations

from pathlib import Path
import time
import shutil

ROOT = Path(".dr_rd")
TEL_DIR = ROOT / "telemetry"
RUNS_DIR = ROOT / "runs"


def purge_telemetry_older_than(days: int) -> int:
    if days < 0:
        return 0
    cutoff = time.time() - days * 86400
    removed = 0
    for p in TEL_DIR.glob("events-*.jsonl*"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink(missing_ok=True)
                removed += 1
        except Exception:
            pass
    return removed


def delete_run(run_id: str) -> bool:
    p = RUNS_DIR / run_id
    if not p.exists():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True


def purge_runs_older_than(days: int) -> int:
    cutoff = time.time() - days * 86400
    removed = 0
    for d in RUNS_DIR.glob("*"):
        try:
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
        except Exception:
            pass
    return removed


def delete_run_events(run_id: str) -> int:
    """Rewrite telemetry files removing lines with the run_id. Returns count of rewritten files."""
    if not TEL_DIR.exists():
        return 0
    rewritten = 0
    for p in TEL_DIR.glob("events-*.jsonl*"):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
            kept = [ln for ln in lines if f"\"run_id\":\"{run_id}\"" not in ln]
            if len(kept) != len(lines):
                p.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
                rewritten += 1
        except Exception:
            pass
    return rewritten


__all__ = [
    "purge_telemetry_older_than",
    "delete_run",
    "purge_runs_older_than",
    "delete_run_events",
]

