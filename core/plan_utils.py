import json
from typing import Any, Dict, List
from .roles import canonicalize, normalize_role

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
            if not role or not isinstance(items, list):
                continue
            for it in items:
                task = {
                    "role": role,
                    "title": (it or {}).get("title", ""),
                    "description": (it or {}).get("description", ""),
                }
                if (it or {}).get("tool_request"):
                    task["tool_request"] = (it or {}).get("tool_request")
                out.append(task)
        return out
    if isinstance(raw, list):
        return list(raw)
    return []

def normalize_plan_to_tasks(raw: Any) -> List[Dict[str, Any]]:
    items = _coerce_to_list(raw)
    out: List[Dict[str, Any]] = []
    for it in items:
        role = canonicalize(normalize_role((it or {}).get("role")))
        title = (it or {}).get("title", "") or ""
        desc = (it or {}).get("description", "") or ""
        # Filter out the “exploded char stream” and junk:
        if not role:
            continue  # e.g., "role"/"title"/"description" as role -> drop
        if len(title.strip()) < 3 or len(desc.strip()) < 3:
            continue
        task = {
            "role": role,
            "title": title.strip(),
            "description": desc.strip(),
        }
        if it.get("tool_request"):
            task["tool_request"] = it.get("tool_request")
        out.append(task)
    return out

def normalize_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Canonicalize roles and deduplicate tasks."""
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for t in tasks:
        role = canonicalize(normalize_role((t or {}).get("role")))
        title = (t or {}).get("title", "")
        desc = (t or {}).get("description", "")
        if not role:
            continue
        key = (role, title, desc, json.dumps(t.get("tool_request", {}), sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        task = {
            "role": role,
            "title": title,
            "description": desc,
        }
        if t.get("tool_request"):
            task["tool_request"] = t.get("tool_request")
        deduped.append(task)
    return deduped
