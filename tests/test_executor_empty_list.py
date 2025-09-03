from types import SimpleNamespace

from core.engine.executor import run_tasks


def test_executor_handles_empty_task_list():
    class State:
        ws = SimpleNamespace(read=lambda: {"results": {}}, save_result=lambda *a, **k: None)

        def _execute(self, task):  # pragma: no cover - not called
            return None, 0.0

    result = run_tasks([], state=State())
    assert result == {}

