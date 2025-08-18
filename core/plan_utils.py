import json
from typing import Any, Dict, List, Tuple

REQUIRED = ("role","title","description")

def _is_task_obj(x: Any) -> bool:
    return isinstance(x, dict) and all(k in x and isinstance(x[k], str) and x[k].strip() for k in REQUIRED)

def coerce_planner_json(raw: Any) -> Any:
    # raw may be JSON string or already-parsed object
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            # try to salvage: grab the first '{' and last '}' slice
            try:
                s = raw[ raw.index("{") : raw.rindex("}")+1 ]
                raw = json.loads(s)
            except Exception:
                return []
    return raw

def normalize_plan_to_tasks(raw: Any) -> List[Dict[str,str]]:
    obj = coerce_planner_json(raw)

    # Case B: already a list of task objects
    if isinstance(obj, list):
        return [t for t in obj if _is_task_obj(t)]

    # Single-object task: {"role","title","description"}  -> wrap into list
    if _is_task_obj(obj):
        return [ {k: obj[k].strip() for k in REQUIRED} ]

    # Case A: {"Role":[{title,description},...], ...}
    tasks: List[Dict[str,str]] = []
    if isinstance(obj, dict):
        for role_key, items in obj.items():
            # only accept lists of dicts; ignore strings to avoid char iteration
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        title = (it.get("title") or "").strip()
                        desc  = (it.get("description") or "").strip()
                        if title and desc:
                            tasks.append({"role": role_key, "title": title, "description": desc})
        return tasks

    return []

# Optional: role normalization (alias -> canonical)
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
        r = normalize_role(t["role"])
        if r and t["title"].strip() and t["description"].strip():
            out.append({"role": r, "title": t["title"].strip(), "description": t["description"].strip()})
    return out
