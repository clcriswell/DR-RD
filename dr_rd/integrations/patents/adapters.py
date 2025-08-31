from __future__ import annotations

from typing import Any, Dict, List

import requests

from dr_rd.config.env import get_env
from . import normalizer


def _http_get_json(url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _search_patentsview(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = "https://api.patentsview.org/patents/query"
    params = query.copy()
    timeout = int(caps.get("timeouts_s", 10))
    data = _http_get_json(url, params=params, timeout=timeout)
    patents = data.get("patents", [])
    return [normalizer.normalize_patent("patentsview", p) for p in patents]


def _search_epo_ops(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = "https://ops.epo.org/3.2/rest-services/published-data/search"
    params = query.copy()
    timeout = int(caps.get("timeouts_s", 10))
    headers = {}
    key = get_env("EPO_OPS_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    records = data.get("ops:world-patent-data", {}).get("ops:biblio-search", {}).get("ops:search-result", {}).get("ops:publication-reference", [])
    return [normalizer.normalize_patent("epo_ops", r) for r in records]


def search_patents(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    backends = caps.get("backends", ["patentsview"])
    max_results = int(caps.get("max_results", 50))
    results: List[Dict[str, Any]] = []
    for backend in backends:
        if backend == "patentsview":
            results.extend(_search_patentsview(query, caps))
        elif backend == "epo_ops":
            results.extend(_search_epo_ops(query, caps))
        if len(results) >= max_results:
            break
    return results[:max_results]
