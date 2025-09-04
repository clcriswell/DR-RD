import pytest

from core.agents.runtime import invoke_agent_safely
from utils import paths, trace_writer


class TaskOnly:
    def __call__(self, task):
        return task["id"]


class TaskModel:
    def run(self, task, model):
        return model


class TaskModelMeta:
    def act(self, task, model, meta):
        return meta["foo"]


class SpecOnly:
    def __call__(self, spec):
        return spec["id"]


class TaskFields:
    def __call__(self, idea, requirements, tests, defects):
        return idea, requirements, tests, defects


class BadAgent:
    pass


@pytest.mark.parametrize(
    "agent, kwargs, expected",
    [
        (TaskOnly(), {}, "T"),
        (TaskModel(), {"model": "m"}, "m"),
        (TaskModelMeta(), {"model": "m", "meta": {"foo": "bar"}}, "bar"),
        (SpecOnly(), {}, "T"),
    ],
)
def test_invoke_agent_variants(agent, kwargs, expected):
    task = {"id": "T", "role": "X"}
    assert invoke_agent_safely(agent, task, **kwargs) == expected


def test_passes_named_task_fields():
    agent = TaskFields()
    task = {
        "id": "T3",
        "role": "Z",
        "idea": "concept",
        "requirements": ["r1"],
        "tests": ["t1"],
        "defects": ["d1"],
    }
    assert invoke_agent_safely(agent, task) == (
        "concept",
        ["r1"],
        ["t1"],
        ["d1"],
    )


def test_uncallable_agent_logs_error(tmp_path):
    paths.RUNS_ROOT = tmp_path / ".dr_rd" / "runs"
    task = {"id": "T2", "role": "Y"}
    with pytest.raises(RuntimeError):
        invoke_agent_safely(BadAgent(), task)
    trace = trace_writer.read_trace("")
    assert any(e.get("event") == "agent_error" for e in trace)
