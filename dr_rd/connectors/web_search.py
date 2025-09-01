"""Provider agnostic web search stub."""

from __future__ import annotations

from typing import List

import logging

from dr_rd.config.env import get_env
from config import feature_flags as ff
from dr_rd.rag.types import Doc
from .commons import use_fixtures, load_fixture
from utils.clients import get_cloud_logging_client


def search_web(query: str, k: int, freshness_days: int | None = None, site_filters=None) -> List[Doc]:
    if use_fixtures():
        data = load_fixture("web_search") or {"items": []}
        docs = []
        for item in data.get("items", []):
            docs.append(
                Doc(
                    id=item.get("url", "0"),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    domain="example.com",
                    published_at=None,
                    text="",
                    meta={},
                )
            )
        return docs
    if not getattr(ff, "ENABLE_LIVE_SEARCH", False):
        raise RuntimeError("live search disabled")
    if not (get_env("BING_API_KEY") or get_env("SERPAPI_KEY")):
        message = "no web search API key"
        logging.error(message)
        try:
            client = get_cloud_logging_client()
            if client:
                client.logger("drrd").log_text(message, severity="ERROR")
        except Exception:
            pass
        return []
    raise RuntimeError("web search not implemented in tests")
