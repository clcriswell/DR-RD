import pytest

import pytest

from core.agents.runtime import invoke_agent_safely
from utils import trace_writer, paths


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
        return spec["task"]["id"]


class BadAgent:
    pass


@pytest.mark.parametrize(
    "agent, kwargs, expected",
    [
        (TaskOnly(), {}, "T"),
        (TaskModel(), {"model": "m"}, "m"),
        (TaskModelMeta(), {"model": "m", "meta": {"foo": "bar"}}, "bar"),
        (SpecOnly(), {"model": "m"}, "T"),
    ],
)
def test_invoke_agent_variants(agent, kwargs, expected, tmp_path, monkeypatch):
    paths.RUNS_ROOT = tmp_path
    task = {"id": "T", "role": "X"}
    assert invoke_agent_safely(agent, task, run_id="R1", **kwargs) == expected


def test_uncallable_agent_logs_error(tmp_path, monkeypatch):
    paths.RUNS_ROOT = tmp_path
    paths.ensure_run_dirs("R2")
    task = {"id": "T2", "role": "Y"}
    with pytest.raises(RuntimeError):
        invoke_agent_safely(BadAgent(), task, run_id="R2")
    trace = trace_writer.read_trace("R2")
    assert any(e.get("event") == "agent_error" for e in trace)
