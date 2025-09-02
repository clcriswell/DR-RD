from typing import Any, Dict, List
import json

from core.roles import normalize_role, canonical_roles

_CANON = canonical_roles()


def _canon_role(name: str) -> str | None:
    return normalize_role(name)


def _is_task(d: Any) -> bool:
    return isinstance(d, dict) and all(
        isinstance(d.get(k, ""), str) and d.get(k, "").strip() for k in ("role", "title", "description")
    )


def _coerce(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            try:
                s = raw[raw.index("{") : raw.rindex("}") + 1]
                return json.loads(s)
            except Exception:
                return []
    return []


def normalize_plan_to_tasks(raw: Any, backfill: bool = True, dedupe: bool = True) -> List[Dict[str, str]]:
    obj = _coerce(raw)
    tasks: List[Dict[str, str]] = []

    # Case B: already a list of tasks
    if isinstance(obj, list):
        for it in obj:
            if _is_task(it):
                role = _canon_role(it["role"])
                if role:
                    tasks.append(
                        {"role": role, "title": it["title"].strip(), "description": it["description"].strip()}
                    )
        return _post(tasks, backfill, dedupe)

    # Single-object task -> wrap
    if _is_task(obj):
        role = _canon_role(obj["role"])
        if role:
            tasks.append(
                {"role": role, "title": obj["title"].strip(), "description": obj["description"].strip()}
            )
        return _post(tasks, backfill, dedupe)

    # Case A: {"Role":[{title,description},...], ...}
    if isinstance(obj, dict):
        for role_key, items in obj.items():
            role = _canon_role(str(role_key))
            if not role:
                continue
            if not isinstance(items, list):  # critical guard: do not iterate strings
                continue
            for it in items:
                if isinstance(it, dict):
                    t = (it.get("title") or "").strip()
                    d = (it.get("description") or "").strip()
                    if t and d:
                        tasks.append({"role": role, "title": t, "description": d})
    return _post(tasks, backfill, dedupe)


def _post(tasks: List[Dict[str, str]], backfill: bool, dedupe: bool) -> List[Dict[str, str]]:
    if dedupe:
        seen = set()
        uniq = []
        for t in tasks:
            k = (t["role"], t["title"])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(t)
        tasks = uniq
    if backfill:
        present = {t["role"] for t in tasks}
        for miss in sorted(_CANON - present):
            tasks.append(
                {
                    "role": miss,
                    "title": f"Define initial {miss} workplan",
                    "description": f"Draft first actionable tasks for {miss} to advance the project.",
                }
            )
    for t in tasks:
        t.setdefault("field", t["role"].lower().replace(" ", "_"))
        t.setdefault("context", t.get("description", ""))
    return tasks

