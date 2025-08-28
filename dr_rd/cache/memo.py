from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple


class MemoCache:
    """In-process memoization with a simple TTL."""

    def __init__(self, ttl: float = 30.0) -> None:
        self.ttl = ttl
        self._store: Dict[Tuple, Tuple[float, Any]] = {}

    def get(self, key: Tuple) -> Any:
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: Tuple, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def get_or_set(self, key: Tuple, builder: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = builder()
        self.set(key, value)
        return value
