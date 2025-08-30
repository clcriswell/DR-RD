from __future__ import annotations

from pathlib import Path

RUNS_ROOT = Path(".dr_rd") / "runs"


def run_root(run_id: str) -> Path:
    """Return the root directory for a run."""
    return RUNS_ROOT / run_id


def artifact_path(run_id: str, name: str, ext: str) -> Path:
    """Return path for a named artifact within a run."""
    return run_root(run_id) / f"{name}.{ext}"


def ensure_run_dirs(run_id: str) -> None:
    """Ensure the run directory exists."""
    run_root(run_id).mkdir(parents=True, exist_ok=True)


def write_bytes(run_id: str, name: str, ext: str, data: bytes) -> Path:
    """Write bytes to a run artifact and return its path."""
    ensure_run_dirs(run_id)
    path = artifact_path(run_id, name, ext)
    path.write_bytes(data)
    return path


def write_text(run_id: str, name: str, ext: str, text: str, encoding: str = "utf-8") -> Path:
    """Write text to a run artifact and return its path."""
    return write_bytes(run_id, name, ext, text.encode(encoding))
