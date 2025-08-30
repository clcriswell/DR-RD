from __future__ import annotations

"""Pluggable artifact storage interface and helpers."""

from dataclasses import dataclass
from typing import Iterable, Optional, Dict, Tuple

from . import prefs


@dataclass(frozen=True)
class ObjRef:
    key: str
    size: Optional[int] = None
    etag: Optional[str] = None
    url: Optional[str] = None


class Storage:
    """Abstract storage backend."""

    backend: str = "unknown"

    def write_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> ObjRef:  # pragma: no cover - interface
        raise NotImplementedError

    def write_text(self, key: str, text: str, *, content_type: str = "text/plain; charset=utf-8") -> ObjRef:  # pragma: no cover - interface
        return self.write_bytes(key, text.encode("utf-8"), content_type=content_type)

    def read_bytes(self, key: str) -> bytes:  # pragma: no cover - interface
        raise NotImplementedError

    def read_text(self, key: str) -> str:
        return self.read_bytes(key).decode("utf-8")

    def exists(self, key: str) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    def list(self, prefix: str) -> Iterable[ObjRef]:  # pragma: no cover - interface
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def url_for(self, key: str, ttl_sec: int) -> Optional[str]:  # pragma: no cover - interface
        return None


_STORAGE: Storage | None = None


def _create_storage(conf: Dict | None) -> Storage:
    backend = (conf or {}).get("backend", "local")
    if backend == "s3":
        from .storage_backends.s3 import S3Storage

        return S3Storage(conf or {})
    if backend == "gcs":
        from .storage_backends.gcs import GCSStorage

        return GCSStorage(conf or {})
    from .storage_backends.localfs import LocalFSStorage

    return LocalFSStorage(conf or {})


def get_storage() -> Storage:
    global _STORAGE
    if _STORAGE is None:
        conf = prefs.load_prefs().get("storage", {})
        _STORAGE = _create_storage(conf)
    return _STORAGE


def key_run(run_id: str, name: str, ext: str) -> str:
    return f"runs/{run_id}/{name}.{ext}"


def key_knowledge(name: str) -> str:
    return f"knowledge/uploads/{name}"
