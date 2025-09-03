from types import SimpleNamespace

from core.engine.executor import run_tasks


def test_executor_empty_guard(monkeypatch):
    created = {}

    class DummyPool:
        def __init__(self, *_, **kw):
            created["max_workers"] = kw.get("max_workers")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, *a, **k):
            from concurrent.futures import Future

            fut = Future()
            fut.set_result((None, 0.0))
            return fut

    monkeypatch.setattr("core.engine.executor.ThreadPoolExecutor", DummyPool)

    class State:
        ws = SimpleNamespace(read=lambda: {"results": {}}, save_result=lambda *a, **k: None)

        def _execute(self, task):  # pragma: no cover - never called in first run
            return None, 0.0

    res = run_tasks([], State())
    assert res == {"executed": [], "pending": []}
    assert "max_workers" not in created

    run_tasks([{"id": "T01", "role": "x", "task": "do"}], State())
    assert created["max_workers"] >= 1

