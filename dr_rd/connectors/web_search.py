"""Provider agnostic web search stub."""

from __future__ import annotations

from typing import List
import os

from config import feature_flags as ff
from dr_rd.rag.types import Doc


def search_web(query: str, k: int, freshness_days: int | None = None, site_filters=None) -> List[Doc]:
    if not getattr(ff, "ENABLE_LIVE_SEARCH", False):
        raise RuntimeError("live search disabled")
    if not (os.getenv("BING_API_KEY") or os.getenv("SERPAPI_KEY")):
        raise RuntimeError("no web search API key")
    raise RuntimeError("web search not implemented in tests")
