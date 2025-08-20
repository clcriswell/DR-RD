import time

from core.engine.executor import run_tasks


class DummyWS:
    def __init__(self):
        self._results = {}

    def read(self):
        return {"results": {k: v[0] for k, v in self._results.items()}}

    def save_result(self, tid, result, score):
        self._results[tid] = (result, score)


class DummyState:
    def __init__(self):
        self.ws = DummyWS()

    def _execute(self, task):
        time.sleep(0.1)
        return f"{task['id']}_done", 1.0


def run_sequential(tasks):
    state = DummyState()
    pending = list(tasks)
    while pending:
        t = pending.pop(0)
        if any(dep not in state.ws.read()["results"] for dep in t.get("depends_on", [])):
            pending.append(t)
            continue
        state.ws.save_result(t["id"], *state._execute(t))
    return state


def run_parallel(tasks):
    state = DummyState()
    pending = list(tasks)
    while pending:
        executed, pending = run_tasks(pending, 2, state)
        pending = list(pending)
    return state


def test_executor_dag_equivalence():
    tasks = [
        {"id": "A", "task": "A", "role": "r", "created_at": 1, "priority": 0},
        {"id": "B", "task": "B", "role": "r", "created_at": 2, "priority": 0},
        {
            "id": "C",
            "task": "C",
            "role": "r",
            "created_at": 3,
            "priority": 0,
            "depends_on": ["A", "B"],
        },
    ]

    seq_state = run_sequential(tasks)
    par_state = run_parallel(tasks)

    assert seq_state.ws._results == par_state.ws._results
    assert len(par_state.ws._results) == 3

    # Parallel execution should be faster than sequential for independent tasks
    start = time.time()
    run_parallel(tasks)
    par_time = time.time() - start

    start = time.time()
    run_sequential(tasks)
    seq_time = time.time() - start

    assert par_time < seq_time
