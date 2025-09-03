from core.engine.executor import run_tasks


def test_executor_zero_guard():
    res = run_tasks([], None)
    assert res == {"executed": [], "pending": []}
