from __future__ import annotations

"""Aggregate metrics across multiple projects for the dashboard."""

from typing import Dict, Iterable, List, Mapping, Optional

from config.feature_flags import DASHBOARD_MAX_COMPARE, DASHBOARD_MAX_PROJECTS

# In-memory fallback store used when an external database (e.g. Firestore) is
# unavailable. Tests inject their own structures so this global remains empty by
# default.
MEMORY_PROJECTS: Dict[str, Mapping[str, object]] = {}


def list_projects(db_or_memory: Optional[Mapping[str, Mapping[str, object]]] = None) -> List[Dict[str, object]]:
    """Return a list of known projects.

    ``db_or_memory`` may be a mapping representing an in-memory store.  When
    ``None`` the module-level ``MEMORY_PROJECTS`` is used.  Only the first
    ``DASHBOARD_MAX_PROJECTS`` entries are returned.
    """

    store = db_or_memory or MEMORY_PROJECTS
    projects = []
    for name, meta in store.items():
        projects.append({"id": name, **(meta or {})})
        if len(projects) >= DASHBOARD_MAX_PROJECTS:
            break
    return projects


def collect_project_metrics(project: Mapping[str, object]) -> Dict[str, float]:
    """Collect roll-up metrics from ``project`` data."""

    runs: Iterable[Mapping[str, object]] = project.get("runs", [])  # type: ignore[index]
    last_run_ts = max((r.get("ts", 0) for r in runs), default=0)
    tasks_count = sum(r.get("tasks", 0) for r in runs)
    tool_calls = sum(r.get("tool_calls", 0) for r in runs)
    retrieval_calls = sum(r.get("retrieval_calls", 0) for r in runs)
    total_cost_usd = sum(r.get("cost_usd", 0.0) for r in runs)
    wall_time_s = sum(r.get("wall_time_s", 0.0) for r in runs)
    scores = [r.get("evaluator_score") for r in runs if r.get("evaluator_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "last_run_ts": last_run_ts,
        "tasks_count": tasks_count,
        "avg_evaluator_score": avg_score,
        "tool_calls": tool_calls,
        "retrieval_calls": retrieval_calls,
        "total_cost_usd": total_cost_usd,
        "wall_time_s": wall_time_s,
    }


def compare_projects(project_ids: List[str], store: Optional[Mapping[str, Mapping[str, object]]] = None) -> Dict[str, Dict[str, float]]:
    """Return metrics for the specified projects.

    Only the first ``DASHBOARD_MAX_COMPARE`` project ids are considered.
    """

    if len(project_ids) > DASHBOARD_MAX_COMPARE:
        project_ids = project_ids[:DASHBOARD_MAX_COMPARE]
    store = store or MEMORY_PROJECTS
    out: Dict[str, Dict[str, float]] = {}
    for pid in project_ids:
        proj = store.get(pid)
        if not proj:
            continue
        out[pid] = collect_project_metrics(proj)
    return out
