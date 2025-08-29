from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

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
    resp = http_get(url, params=params, headers=headers, retries=retries, timeout=timeout)
    return resp.json()


def signed_headers(key_env: str, headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(headers or {})
    key = os.getenv(key_env)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def load_fixture(name: str, fixtures_dir: Path | None = None) -> dict[str, Any]:
    """Load a JSON fixture for demos or tests.

    Parameters
    ----------
    name: str
        Path to the fixture relative to the fixtures directory.
    fixtures_dir: Path | None
        Base directory containing fixtures. Defaults to ``tests/fixtures/connectors``
        located relative to this file. Set the ``DEMO_FIXTURES_DIR`` environment
        variable to override this location.

    Returns
    -------
    dict[str, Any]
        Parsed JSON content of the fixture.
    """

    if fixtures_dir is None:
        env_dir = os.getenv("DEMO_FIXTURES_DIR")
        if env_dir:
            fixtures_dir = Path(env_dir)
        else:
            fixtures_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "connectors"
    path = fixtures_dir / name
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


__all__ = [
    "cached",
    "http_get",
    "http_json",
    "ratelimit_guard",
    "signed_headers",
    "load_fixture",
]
