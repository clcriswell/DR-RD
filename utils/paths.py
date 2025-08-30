from __future__ import annotations

"""Thin wrapper around storage for run artifacts."""

from pathlib import Path
from typing import Iterable

from .storage import get_storage, key_run


def artifact_key(run_id: str, name: str, ext: str) -> str:
    return key_run(run_id, name, ext)


def write_bytes(run_id: str, name: str, ext: str, data: bytes) -> Path:
    """Write bytes to storage and return a local path when available."""
    ref = get_storage().write_bytes(artifact_key(run_id, name, ext), data)
    local = local_path_for_debug(ref.key)
    return local if local is not None else Path(ref.key)


def write_text(run_id: str, name: str, ext: str, text: str) -> Path:
    """Write text to storage and return a local path when available."""
    ref = get_storage().write_text(artifact_key(run_id, name, ext), text)
    local = local_path_for_debug(ref.key)
    return local if local is not None else Path(ref.key)


def read_bytes(run_id: str, name: str, ext: str) -> bytes:
    return get_storage().read_bytes(artifact_key(run_id, name, ext))


def read_text(run_id: str, name: str, ext: str) -> str:
    return get_storage().read_text(artifact_key(run_id, name, ext))


def exists(run_id: str, name: str, ext: str) -> bool:
    return get_storage().exists(artifact_key(run_id, name, ext))


def list_run(run_id: str) -> Iterable[str]:
    prefix = f"runs/{run_id}"
    for ref in get_storage().list(prefix):
        yield ref.key


def local_path_for_debug(key: str) -> Path | None:
    storage = get_storage()
    if storage.backend == "local":
        from .storage_backends.localfs import LocalFSStorage
        assert isinstance(storage, LocalFSStorage)
        return storage.root / key
    return None


# Compatibility helpers -----------------------------------------------------
RUNS_ROOT = Path(".dr_rd") / "runs"


def run_root(run_id: str) -> Path:
    """Return the directory for a run without creating it."""
    return RUNS_ROOT / run_id


def ensure_run_dirs(run_id: str) -> Path:
    path = run_root(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_path(run_id: str, name: str, ext: str) -> Path:
    return ensure_run_dirs(run_id) / f"{name}.{ext}"
