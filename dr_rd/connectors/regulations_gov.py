from __future__ import annotations

from typing import Any, Dict, Optional

from .commons import cached, http_json, ratelimit_guard, signed_headers

BASE_URL = "https://api.regulations.gov/v4/documents"


def _normalize(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "authority": "US",
        "agency": item.get("agency"),
        "docket_id": item.get("docket_id"),
        "cfr_refs": item.get("cfr_references", []),
        "rule_stage": item.get("rule_stage"),
        "effective_date": item.get("effective_date"),
        "summary": item.get("summary"),
        "url": item.get("url"),
    }


@cached(ttl_s=86400)
def search_documents(query: str) -> Dict[str, Any]:
    ratelimit_guard("reg_gov_search", 5)
    params = {"q": query}
    headers = signed_headers("REG_GOV_API_KEY")
    data = http_json(BASE_URL, params=params, headers=headers)
    records = [_normalize(d) for d in data.get("data", [])]
    return {"items": records}


@cached(ttl_s=86400)
def fetch_document(document_id: str) -> Dict[str, Any]:
    ratelimit_guard("reg_gov_fetch", 5)
    headers = signed_headers("REG_GOV_API_KEY")
    data = http_json(f"{BASE_URL}/{document_id}", headers=headers)
    return {"record": _normalize(data.get("data", {}))}


__all__ = ["search_documents", "fetch_document"]
