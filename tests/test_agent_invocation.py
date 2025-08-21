import pytest

from core.agents.invoke import resolve_invoker


class NoIface:
    pass


class Runs:
    def run(self, *, task, model: str | None = None):
        return task["x"]


def test_missing_interface():
    with pytest.raises(TypeError) as exc:
        resolve_invoker(NoIface())
    assert "no callable interface" in str(exc.value)


def test_run_invocation():
    name, inv = resolve_invoker(Runs())
    assert name == "run"
    assert inv(task={"x": 1}, model="m") == 1
