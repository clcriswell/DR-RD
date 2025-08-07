"""Parallel task execution utilities for the DR-RD engine.

This module exposes a ``run_tasks`` helper that schedules independent tasks for
concurrent execution while ensuring that merges back into the shared state are
performed deterministically.  It purposefully avoids mutating shared state from
worker threads; only the orchestrator thread performs state mutations.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterable, List, Tuple


Task = Dict[str, Any]
TaskResult = Tuple[Task, Any, float]  # (task, result, score)


def _deps_satisfied(task: Task, state: Dict[str, Any]) -> bool:
    """Return ``True`` if all dependencies for ``task`` have been satisfied."""
    deps: Iterable[str] = task.get("depends_on", [])
    if not deps:
        return True
    completed = state.get("results", {})
    return all(d in completed for d in deps)


def _sort_key(item: TaskResult) -> Tuple[int, float, str]:
    """Sorting key implementing the deterministic merge policy."""
    t = item[0]
    return (-int(t.get("priority", 0)), float(t.get("created_at", 0)), t.get("id", ""))


def merge_results(state: Any, task: Task, result: Any, score: float, log: Callable[[str], None] | None = None) -> None:
    """Merge ``result`` for ``task`` into ``state`` with basic conflict resolution."""
    existing = state.ws.read().get("results", {})
    if task["id"] in existing and log:
        log(f"⚠️ conflict for task {task['id']} – overwriting previous result")
    state.ws.save_result(task["id"], result, score)


def run_tasks(
    tasks: List[Task],
    max_workers: int,
    state: Any,
    log: Callable[[str], None] | None = None,
) -> Tuple[List[Tuple[Task, float]], List[Task]]:
    """Execute ``tasks`` concurrently when possible.

    Parameters
    ----------
    tasks:
        Tasks to consider for execution. Each task is a ``dict`` containing at
        least ``id`` and ``task`` fields. Optional fields include ``priority``,
        ``created_at`` and ``depends_on``.
    max_workers:
        Maximum number of worker threads to use.
    state:
        Orchestrator state that exposes ``_execute`` and ``ws`` (workspace).
    log:
        Optional logger used for maintaining the existing log format.

    Returns
    -------
    executed, pending:
        ``executed`` is a list of ``(task, score)`` tuples for tasks that were
        run. ``pending`` contains tasks whose dependencies were not yet
        satisfied.
    """

    ready: List[Task] = []
    pending: List[Task] = []
    current_state = state.ws.read()

    for t in tasks:
        if _deps_satisfied(t, current_state):
            ready.append(t)
            if log:
                log(f"▶️ {t['role']} – {t['task'][:60]}…")
        else:
            pending.append(t)

    results: List[TaskResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(state._execute, t): t for t in ready}
        for fut in as_completed(future_map):
            task = future_map[fut]
            res, score = fut.result()
            results.append((task, res, score))

    executed: List[Tuple[Task, float]] = []
    for task, res, score in sorted(results, key=_sort_key):
        merge_results(state, task, res, score, log)
        executed.append((task, score))

    return executed, pending
