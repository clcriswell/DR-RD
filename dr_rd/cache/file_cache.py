from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional


class FileCache:
    """A tiny TTL-based file cache storing JSON serialisable values."""

    def __init__(self, root: Path | None = None):
        root = root or Path(os.getenv("DRRD_CACHE_DIR", ".cache"))
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{h}.json"

    def get(self, key: str, ttl_s: int) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
            if time.time() - float(payload.get("ts", 0)) > ttl_s:
                return None
            return payload.get("value")
        except Exception:
            return None

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        payload = {"ts": time.time(), "value": value}
        path.write_text(json.dumps(payload))


def cached(ttl_s: int, cache: FileCache | None = None) -> Callable:
    cache = cache or FileCache()

    def decorator(fn: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{fn.__module__}.{fn.__name__}:{json.dumps([args, kwargs], sort_keys=True, default=str)}"
            cached_value = cache.get(key, ttl_s)
            if cached_value is not None:
                return cached_value
            value = fn(*args, **kwargs)
            cache.set(key, value)
            return value

        return wrapper

    return decorator


__all__ = ["FileCache", "cached"]
