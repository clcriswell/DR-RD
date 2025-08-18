from typing import Any, Dict, List
import json

REQUIRED = ("role","title","description")

def _is_task_obj(x: Any) -> bool:
    return isinstance(x, dict) and all(isinstance(x.get(k,""), str) and x.get(k, "").strip() for k in REQUIRED)

def _coerce(raw: Any) -> Any:
    if isinstance(raw, (dict, list)): return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            try:
                s = raw[ raw.index("{") : raw.rindex("}")+1 ]
                return json.loads(s)
            except Exception:
                return []
    return []

def normalize_plan_to_tasks(raw: Any) -> List[Dict[str,str]]:
    obj = _coerce(raw)

    # Case B: already a list of tasks
    if isinstance(obj, list):
        return [ {k: t[k].strip() for k in REQUIRED} for t in obj if _is_task_obj(t) ]

    # Single-object task -> wrap
    if _is_task_obj(obj):
        return [ {k: obj[k].strip() for k in REQUIRED} ]

    # Case A: {"Role":[{title,description},...], ...}
    tasks: List[Dict[str,str]] = []
    if isinstance(obj, dict):
        for role_key, items in obj.items():
            if not isinstance(items, list):  # ignore strings to avoid char-splitting
                continue
            for it in items:
                if isinstance(it, dict):
                    title = (it.get("title") or "").strip()
                    desc  = (it.get("description") or "").strip()
                    if title and desc:
                        tasks.append({"role": str(role_key), "title": title, "description": desc})
    return tasks

# Simple alias map (keep as-is or extend)
ROLE_MAP = {
    "cto":"CTO","chief technology officer":"CTO",
    "research":"Research Scientist","research scientist":"Research Scientist",
    "regulatory":"Regulatory","regulatory & compliance lead":"Regulatory","compliance":"Regulatory","legal":"Regulatory",
    "finance":"Finance",
    "marketing":"Marketing Analyst","marketing analyst":"Marketing Analyst",
    "ip":"IP Analyst","ip analyst":"IP Analyst","intellectual property":"IP Analyst",
}
def normalize_role(name: str) -> str:
    return ROLE_MAP.get((name or "").strip().lower(), name or "")

def normalize_tasks(tasks: List[Dict[str,str]]) -> List[Dict[str,str]]:
    out=[]
    for t in tasks:
        role = normalize_role(t.get("role", ""))
        title = (t.get("title", "")).strip()
        desc = (t.get("description", "")).strip()
        if role and title and desc:
            out.append({"role": role, "title": title, "description": desc})
    return out
