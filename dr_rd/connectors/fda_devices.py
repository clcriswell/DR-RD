from __future__ import annotations

from typing import Any, Dict

from .commons import cached, http_json, ratelimit_guard, signed_headers

BASE_URL = "https://api.fda.gov/device/510k.json"


def _normalize(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "k_number": item.get("k_number"),
        "device_name": item.get("device_name"),
        "applicant": item.get("applicant"),
        "decision_date": item.get("decision_date"),
        "regulation_number": item.get("regulation_number"),
        "url": item.get("url"),
    }


@cached(ttl_s=86400)
def search_devices(query: str) -> Dict[str, Any]:
    ratelimit_guard("fda_device_search", 5)
    params = {"search": query}
    headers = signed_headers("FDA_API_KEY")
    data = http_json(BASE_URL, params=params, headers=headers)
    records = [_normalize(r) for r in data.get("results", [])]
    return {"items": records}


__all__ = ["search_devices"]
