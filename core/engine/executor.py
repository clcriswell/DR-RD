"""Parallel task execution utilities for the DR-RD engine.

The :func:`run_tasks` helper schedules independent tasks for concurrent
execution while ensuring deterministic merging of results.  It purposefully
avoids mutating shared state from worker threads; only the orchestrator thread
performs state mutations.  The unified orchestrator uses this helper when
``PARALLEL_EXEC_ENABLED`` is set to ``True``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from utils.telemetry import tasks_executable

Task = dict[str, Any]
TaskResult = tuple[Task, Any, float]  # (task, result, score)


def _deps_satisfied(task: Task, state: dict[str, Any]) -> bool:
    """Return ``True`` if all dependencies for ``task`` have been satisfied."""
    deps: Iterable[str] = task.get("depends_on", [])
    if not deps:
        return True
    completed = state.get("results", {})
    return all(d in completed for d in deps)


def _sort_key(item: TaskResult) -> tuple[int, float, str]:
    """Sorting key implementing the deterministic merge policy."""
    t = item[0]
    return (-int(t.get("priority", 0)), float(t.get("created_at", 0)), t.get("id", ""))


def merge_results(
    state: Any, task: Task, result: Any, score: float, log: Callable[[str], None] | None = None
) -> None:
    """Merge ``result`` for ``task`` into ``state`` with basic conflict resolution."""
    existing = state.ws.read().get("results", {})
    if task["id"] in existing and log:
        log(f"⚠️ conflict for task {task['id']} – overwriting previous result")
    state.ws.save_result(task["id"], result, score)


def run_tasks(
    tasks: list[Task],
    state: Any,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute ``tasks`` concurrently when possible.

    Returns a dict with ``executed`` and ``pending`` lists.  If ``tasks`` is
    empty, an empty dict is returned.
    """

    if not tasks:
        return {}

    ready: list[Task] = []
    pending: list[Task] = []
    current_state = state.ws.read()

    for t in tasks:
        if _deps_satisfied(t, current_state):
            ready.append(t)
            if log:
                log(f"▶️ {t['role']} – {t['task'][:60]}…")
        else:
            pending.append(t)
    tasks_executable(len(ready))
    if not ready:
        return {"executed": [], "pending": tasks}

    max_workers = max(1, min(4, len(tasks)))
    results: list[TaskResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(state._execute, t): t for t in ready}
        for fut in as_completed(future_map):
            task = future_map[fut]
            res, score = fut.result()
            results.append((task, res, score))

    executed: list[tuple[Task, float]] = []
    for task, res, score in sorted(results, key=_sort_key):
        merge_results(state, task, res, score, log)
        executed.append((task, score))

    return {"executed": executed, "pending": pending}
