from __future__ import annotations

from typing import Any, Dict, List, Optional

from .commons import cached, http_json, ratelimit_guard, signed_headers

BASE_URL = "https://api.patentsview.org/patents/search"
FETCH_URL = "https://api.patentsview.org/patents/query"


def _normalize(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pub_number": record.get("publication_number"),
        "app_number": record.get("application_number"),
        "title": record.get("title"),
        "abstract": record.get("abstract"),
        "assignees": record.get("assignees", []),
        "inventors": record.get("inventors", []),
        "cpc_codes": record.get("cpcs", []),
        "ipc_codes": record.get("ipcs", []),
        "pub_date": record.get("publication_date"),
        "priority_date": record.get("priority_date"),
        "cited_by_count": record.get("cited_by_count"),
        "citations": record.get("citations", []),
        "url": record.get("url"),
    }


@cached(ttl_s=86400)
def search_patents(query: str) -> Dict[str, Any]:
    ratelimit_guard("uspto_search", 5)
    params = {"q": query}
    headers = signed_headers("USPTO_API_KEY")
    data = http_json(BASE_URL, params=params, headers=headers)
    records = [_normalize(r) for r in data.get("results", [])]
    return {"items": records}


@cached(ttl_s=86400)
def fetch_patent(
    pub_number: Optional[str] = None, app_number: Optional[str] = None
) -> Dict[str, Any]:
    ratelimit_guard("uspto_fetch", 5)
    params: Dict[str, Any] = {}
    if pub_number:
        params["pub_number"] = pub_number
    if app_number:
        params["app_number"] = app_number
    headers = signed_headers("USPTO_API_KEY")
    data = http_json(FETCH_URL, params=params, headers=headers)
    records = [_normalize(data.get("result", {}))]
    return {"record": records[0]}


__all__ = ["search_patents", "fetch_patent"]
