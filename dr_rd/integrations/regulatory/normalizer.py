from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

def _parse_date(val: str | None) -> str | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val[:10]).date().isoformat()
    except Exception:
        return val

def _federal_register(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "federal_register",
        "id": doc.get("document_number"),
        "title": doc.get("title"),
        "citation": doc.get("citation"),
        "jurisdiction": "US",
        "section": doc.get("citation"),
        "url": doc.get("html_url"),
        "date": _parse_date(doc.get("publication_date")),
        "text_snippet": doc.get("snippet"),
    }

def _ecfr(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "ecfr",
        "id": doc.get("identifier"),
        "title": doc.get("title"),
        "citation": doc.get("citation"),
        "jurisdiction": "US",
        "section": doc.get("section"),
        "url": doc.get("url"),
        "date": _parse_date(doc.get("date")),
        "text_snippet": doc.get("text"),
    }

def normalize_regulation(backend: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    if backend == "federal_register":
        return _federal_register(doc)
    if backend == "ecfr":
        return _ecfr(doc)
    return {
        "source": backend,
        "id": doc.get("id"),
        "title": doc.get("title"),
        "citation": doc.get("citation"),
        "jurisdiction": doc.get("jurisdiction"),
        "section": doc.get("section"),
        "url": doc.get("url"),
        "date": _parse_date(doc.get("date")),
        "text_snippet": doc.get("text_snippet"),
    }
