import json
from typing import Any, Dict, List
from .roles import normalize_role, canonical_roles

def _coerce_to_list(raw: Any) -> List[Dict[str, Any]]:
    # Accept str (JSON), dict (single task or role->list), list
    if raw is None:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        try:
            data = json.loads(s)
        except Exception:
            # try to wrap as array
            try:
                data = json.loads(f"[{s}]")
            except Exception:
                return []
        raw = data
    if isinstance(raw, dict):
        # Could be single task object OR role->list mapping
        if {"role","title","description"} <= set(map(str.lower, raw.keys())):
            return [raw]
        # role -> list-of-{title,description}
        out: List[Dict[str, Any]] = []
        for role_key, items in (raw or {}).items():
            role = normalize_role(role_key)
            if not role:
                continue
            for it in items or []:
                out.append({
                    "role": role,
                    "title": (it or {}).get("title",""),
                    "description": (it or {}).get("description",""),
                })
        return out
    if isinstance(raw, list):
        return list(raw)
    return []

def normalize_plan_to_tasks(raw: Any) -> List[Dict[str, str]]:
    items = _coerce_to_list(raw)
    out: List[Dict[str, str]] = []
    for it in items:
        role = normalize_role((it or {}).get("role"))
        title = (it or {}).get("title","") or ""
        desc = (it or {}).get("description","") or ""
        # Filter out the “exploded char stream” and junk:
        if not role:
            continue  # e.g., "role"/"title"/"description" as role -> drop
        if len(title.strip()) < 3 or len(desc.strip()) < 3:
            continue
        out.append({"role": role, "title": title.strip(), "description": desc.strip()})
    return out

def normalize_tasks(tasks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # Deduplicate exact duplicates; keep order
    seen = set()
    deduped = []
    for t in tasks:
        key = (t["role"], t["title"], t["description"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(t)
    return deduped
