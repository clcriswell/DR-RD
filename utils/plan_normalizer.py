from typing import List, Dict, Any


def _normalize_plan_to_tasks(plan) -> List[Dict[str, str]]:
    """
    Returns list of {'role':str,'title':str,'description':str}
    Accepts:
      A) dict: role -> list[ {title,description} | str ]
      B) list of {role,title,description}
    """
    tasks: List[Dict[str, str]] = []
    if isinstance(plan, dict):
        for role, items in plan.items():
            for it in items or []:
                if isinstance(it, str):
                    tasks.append({"role": role, "title": it, "description": it})
                else:
                    tasks.append(
                        {
                            "role": role,
                            "title": it.get("title") or it.get("task") or "",
                            "description": it.get("description")
                            or it.get("details")
                            or it.get("title")
                            or "",
                        }
                    )
    elif isinstance(plan, list):
        for it in plan:
            tasks.append(
                {
                    "role": it.get("role", ""),
                    "title": it.get("title") or it.get("task") or "",
                    "description": it.get("description")
                    or it.get("details")
                    or it.get("title")
                    or "",
                }
            )
    else:
        raise ValueError("Planner returned unexpected plan type")
    return [t for t in tasks if t["title"] or t["description"]]
