"""Utilities for bounded parallelism and retry backoff."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Iterable, Any


class ParallelLimiter:
    """Simple thread-based parallelism limiter."""

    def __init__(self, max_concurrency: int = 1):
        self.max_concurrency = max(1, int(max_concurrency))
        self._executor = ThreadPoolExecutor(max_workers=self.max_concurrency)

    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        return self._executor.submit(fn, *args, **kwargs)


class ExponentialBackoff:
    """Exponential backoff helper."""

    def __init__(self, base_s: float = 1.0, factor: float = 2.0, max_s: float = 30.0):
        self.base = base_s
        self.factor = factor
        self.max = max_s
        self.attempt = 0

    def next(self) -> float:
        delay = min(self.base * (self.factor ** self.attempt), self.max)
        self.attempt += 1
        return delay

    def sleep(self) -> None:
        time.sleep(self.next())

    def reset(self) -> None:
        self.attempt = 0


__all__ = ["ParallelLimiter", "ExponentialBackoff"]
