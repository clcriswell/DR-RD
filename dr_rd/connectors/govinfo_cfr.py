from __future__ import annotations

from typing import Any, Dict

from .commons import (
    cached,
    http_json,
    ratelimit_guard,
    signed_headers,
    use_fixtures,
    load_fixture,
)

BASE_URL = "https://api.govinfo.gov/cfr"  # placeholder


def lookup_cfr(title: str, part: str, section: str) -> Dict[str, Any]:
    if use_fixtures():
        return load_fixture("cfr_lookup") or {
            "title": title,
            "part": part,
            "section": section,
            "text": "",
            "url": "",
        }
    ratelimit_guard("govinfo_cfr", 5)
    params = {"title": title, "part": part, "section": section}
    headers = signed_headers("GOVINFO_API_KEY")
    data = http_json(BASE_URL, params=params, headers=headers)
    return {
        "title": title,
        "part": part,
        "section": section,
        "text": data.get("text"),
        "url": data.get("url"),
    }


lookup_cfr = cached(ttl_s=86400)(lookup_cfr)

__all__ = ["lookup_cfr"]
