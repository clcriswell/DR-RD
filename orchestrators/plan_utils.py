from typing import List, Dict, Any


def normalize_plan_to_tasks(plan: Any) -> List[Dict]:
    """
    Normalize Planner output to a list of {role,title,description,tags}
    Accepts:
      A) dict: role -> list[{title,description}|str]
      B) list of {role,title,description[,tags]}
    """
    tasks: List[Dict] = []
    if isinstance(plan, dict):
        for role, items in (plan or {}).items():
            for it in (items or []):
                if isinstance(it, str):
                    tasks.append({"role": role, "title": it, "description": it, "tags": []})
                else:
                    tasks.append({
                        "role": role,
                        "title": it.get("title") or it.get("task") or "",
                        "description": it.get("description") or it.get("details") or it.get("title") or "",
                        "tags": it.get("tags", []) if isinstance(it, dict) else [],
                    })
    elif isinstance(plan, list):
        for it in plan:
            tasks.append({
                "role": it.get("role",""),
                "title": it.get("title") or it.get("task") or "",
                "description": it.get("description") or it.get("details") or it.get("title") or "",
                "tags": it.get("tags", []) if isinstance(it, dict) else [],
            })
    else:
        raise ValueError("Planner returned unexpected plan type")
    # remove empties
    return [t for t in tasks if (t["title"] or t["description"])]
