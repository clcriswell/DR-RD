from __future__ import annotations

"""Local filesystem storage backend."""

from pathlib import Path
from typing import Iterable, Optional

from ..storage import ObjRef, Storage
from .. import telemetry


class LocalFSStorage(Storage):
    backend = "local"

    def __init__(self, conf: dict | None = None) -> None:
        prefix = (conf or {}).get("prefix", "dr_rd")
        self.root = Path(f".{prefix}")
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        return self.root / key

    def write_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> ObjRef:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        telemetry.storage_write(self.backend, key, len(data))
        return ObjRef(key=key, size=len(data))

    def read_bytes(self, key: str) -> bytes:
        path = self._resolve(key)
        data = path.read_bytes()
        telemetry.storage_read(self.backend, key, len(data))
        return data

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def list(self, prefix: str) -> Iterable[ObjRef]:
        base = self._resolve(prefix)
        if not base.exists():
            return []
        refs: list[ObjRef] = []
        for p in base.rglob("*"):
            if p.is_file():
                rel = p.relative_to(self.root).as_posix()
                refs.append(ObjRef(key=rel, size=p.stat().st_size))
        return refs

    def delete(self, key: str) -> None:
        try:
            self._resolve(key).unlink()
        except FileNotFoundError:
            pass

    def url_for(self, key: str, ttl_sec: int) -> Optional[str]:
        return None
