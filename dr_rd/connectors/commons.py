from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from typing import Any, Dict, Optional

import requests

from dr_rd.cache.file_cache import cached

_RATE_LIMITS: Dict[str, list[float]] = defaultdict(list)


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
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
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
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    retries: int = 3,
    timeout: int = 10,
) -> Dict[str, Any]:
    resp = http_get(url, params=params, headers=headers, retries=retries, timeout=timeout)
    return resp.json()


def signed_headers(key_env: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = dict(headers or {})
    key = os.getenv(key_env)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


__all__ = ["cached", "http_get", "http_json", "ratelimit_guard", "signed_headers"]
