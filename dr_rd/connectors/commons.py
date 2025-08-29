from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from dr_rd.cache.file_cache import cached

_RATE_LIMITS: dict[str, list[float]] = defaultdict(list)


def ratelimit_guard(key: str, limit: int, period_s: int = 60) -> None:
    """Simple in-process rate limit guard."""
    now = time.time()
    window = [t for t in _RATE_LIMITS[key] if now - t < period_s]
    if len(window) >= limit:
        raise RuntimeError("rate limit exceeded")
    window.append(now)
    _RATE_LIMITS[key] = window


def _backoff(attempt: int) -> float:
    return (2**attempt) + random.random()


def http_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    timeout: int = 10,
) -> requests.Response:
    """HTTP GET with basic retry and exponential jitter."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(_backoff(attempt))
    raise RuntimeError("unreachable")


def http_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    timeout: int = 10,
) -> dict[str, Any]:
    if use_fixtures():
        name = os.path.basename(url).split("?")[0]
        fixture = load_fixture(name)
        if fixture is not None:
            return fixture
    resp = http_get(url, params=params, headers=headers, retries=retries, timeout=timeout)
    return resp.json()


def signed_headers(key_env: str, headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(headers or {})
    key = os.getenv(key_env)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def use_fixtures() -> bool:
    """Return True when connectors should read from offline fixtures."""
    if os.getenv("DEMO_FIXTURES_DIR"):
        return True
    if os.getenv("ENABLE_LIVE_SEARCH") in {"0", "false", "False"}:
        return True
    return False


def load_fixture(name: str) -> Optional[Dict[str, Any]]:
    base = os.getenv("DEMO_FIXTURES_DIR")
    if not base:
        base = "samples/connectors/fixtures"
    path = Path(base) / name
    if path.suffix != ".json":
        path = path.with_suffix(".json")
    if path.exists():
        with open(path) as fh:
            return json.load(fh)
    return None


__all__ = [
    "cached",
    "http_get",
    "http_json",
    "ratelimit_guard",
    "signed_headers",
    "use_fixtures",
    "load_fixture",
]
