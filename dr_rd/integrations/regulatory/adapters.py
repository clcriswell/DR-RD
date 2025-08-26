from __future__ import annotations

from typing import Any, Dict, List
import requests

from . import normalizer


def _http_get_json(url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _search_federal_register(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = "https://www.federalregister.gov/api/v1/documents.json"
    timeout = int(caps.get("timeouts_s", 10))
    data = _http_get_json(url, query, timeout)
    docs = data.get("results", [])
    return [normalizer.normalize_regulation("federal_register", d) for d in docs]


def _search_ecfr(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = "https://www.ecfr.gov/api/versioner/v1/full"
    timeout = int(caps.get("timeouts_s", 10))
    data = _http_get_json(url, query, timeout)
    docs = data.get("results", []) if isinstance(data, dict) else []
    return [normalizer.normalize_regulation("ecfr", d) for d in docs]


def _search_eur_lex(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = "https://eur-lex.europa.eu/EURLexWebService"
    timeout = int(caps.get("timeouts_s", 10))
    data = _http_get_json(url, query, timeout)
    docs = data.get("results", []) if isinstance(data, dict) else []
    return [normalizer.normalize_regulation("eur_lex", d) for d in docs]


def search_regulations(query: Dict[str, Any], caps: Dict[str, Any]) -> List[Dict[str, Any]]:
    backends = caps.get("backends", ["federal_register"])
    max_results = int(caps.get("max_results", 50))
    results: List[Dict[str, Any]] = []
    for backend in backends:
        if backend == "federal_register":
            results.extend(_search_federal_register(query, caps))
        elif backend == "ecfr":
            results.extend(_search_ecfr(query, caps))
        elif backend == "eur_lex":
            results.extend(_search_eur_lex(query, caps))
        if len(results) >= max_results:
            break
    return results[:max_results]
