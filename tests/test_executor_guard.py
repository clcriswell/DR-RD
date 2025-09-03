from core.engine import executor as ex


class DummyWS:
    def read(self):
        return {"results": {}}

    def save_result(self, *a, **k):
        pass


class DummyState:
    def __init__(self):
        self.ws = DummyWS()

    def _execute(self, task):
        return "ok", 0.0


def test_run_tasks_empty(monkeypatch):
    called = False

    def fake_pool(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("ThreadPoolExecutor should not be called")

    monkeypatch.setattr(ex, "ThreadPoolExecutor", fake_pool)
    out = ex.run_tasks([], DummyState())
    assert out == {"executed": [], "pending": []}
    assert called is False


def test_run_tasks_max_workers(monkeypatch):
    captured = {}
    orig = ex.ThreadPoolExecutor

    def cap_pool(max_workers, *a, **k):
        captured["mw"] = max_workers
        return orig(max_workers, *a, **k)

    monkeypatch.setattr(ex, "ThreadPoolExecutor", cap_pool)
    tasks = [{"id": "T1", "role": "R", "task": "do"}]
    ex.run_tasks(tasks, DummyState())
    assert captured["mw"] >= 1
