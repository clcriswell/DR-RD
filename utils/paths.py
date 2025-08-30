from __future__ import annotations

"""Thin wrapper around storage for run artifacts."""

from pathlib import Path
from typing import Iterable

from .storage import get_storage, key_run


def artifact_key(run_id: str, name: str, ext: str) -> str:
    return key_run(run_id, name, ext)


def write_bytes(run_id: str, name: str, ext: str, data: bytes) -> str:
    return get_storage().write_bytes(artifact_key(run_id, name, ext), data).key


def write_text(run_id: str, name: str, ext: str, text: str) -> str:
    return get_storage().write_text(artifact_key(run_id, name, ext), text).key


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
