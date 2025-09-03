import time
from types import SimpleNamespace

from core.engine.executor import run_tasks
from concurrent.futures import Future


class DummyState:
    def __init__(self):
        self.ws = SimpleNamespace(read=lambda: {"results": {}}, save_result=lambda *_: None)

    def _execute(self, task):
        time.sleep(0.01)
        return None, 0.0


def test_run_tasks_empty_skips_pool(monkeypatch):
    called = {}

    def fake_pool(max_workers):
        called["max_workers"] = max_workers
        raise AssertionError("pool should not be created")

    monkeypatch.setattr("core.engine.executor.ThreadPoolExecutor", fake_pool)
    executed, pending = run_tasks([], DummyState())
    assert executed == [] and pending == []
    assert "max_workers" not in called


def test_run_tasks_floor_one(monkeypatch):
    seen = {}

    class FakePool:
        def __init__(self, max_workers):
            seen["max_workers"] = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def submit(self, fn, task):
            fut = Future()
            fut.set_result((None, 0.0))
            return fut

    monkeypatch.setattr("core.engine.executor.ThreadPoolExecutor", FakePool)
    run_tasks([{"id": "A", "task": "a", "role": "r"}], DummyState())
    assert seen["max_workers"] == 1
