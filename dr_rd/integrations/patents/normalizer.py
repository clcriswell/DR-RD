from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

def _parse_date(val: str | None) -> str | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val[:10]).date().isoformat()
    except Exception:
        return val

def _parse_cpc(parts: List[Dict[str, Any]] | None) -> List[str]:
    items: List[str] = []
    if not parts:
        return items
    for p in parts:
        code = p.get("cpc_subgroup_id") or p.get("code")
        if code:
            items.append(code)
    return items

def _patentsview(doc: Dict[str, Any]) -> Dict[str, Any]:
    assignee = None
    assignees = doc.get("assignees") or []
    if assignees:
        assignee = assignees[0].get("assignee_organization")
    inventors = [
        f"{i.get('inventor_first_name','')} {i.get('inventor_last_name','')}".strip()
        for i in doc.get("inventors") or []
    ]
    return {
        "source": "patentsview",
        "id": doc.get("patent_number"),
        "title": doc.get("title"),
        "abstract": doc.get("abstract"),
        "assignee": assignee,
        "inventors": inventors,
        "cpc": _parse_cpc(doc.get("cpc_subgroups")),
        "pub_date": _parse_date(doc.get("patent_date")),
        "url": f"https://patentsview.org/patent/{doc.get('patent_number')}",
    }

def _epo_ops(doc: Dict[str, Any]) -> Dict[str, Any]:
    pub = doc.get("publication-reference", {}).get("document-id", [{}])[0]
    title = None
    titles = doc.get("invention-title") or []
    if titles:
        title = titles[0].get("$")
    return {
        "source": "epo_ops",
        "id": pub.get("doc-number"),
        "title": title,
        "abstract": None,
        "assignee": None,
        "inventors": [],
        "cpc": [],
        "pub_date": _parse_date(pub.get("date")),
        "url": "",
    }

def normalize_patent(backend: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    if backend == "patentsview":
        return _patentsview(doc)
    if backend == "epo_ops":
        return _epo_ops(doc)
    return {
        "source": backend,
        "id": doc.get("id"),
        "title": doc.get("title"),
        "abstract": doc.get("abstract"),
        "assignee": doc.get("assignee"),
        "inventors": doc.get("inventors", []),
        "cpc": doc.get("cpc", []),
        "pub_date": _parse_date(doc.get("pub_date")),
        "url": doc.get("url"),
    }
