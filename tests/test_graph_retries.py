import time
from types import SimpleNamespace

import pytest

import config.feature_flags as ff
from dr_rd.evaluation.scorecard import Scorecard


class EvalStub:
    def __init__(self):
        self.calls = 0

    def __call__(self, content, context):
        self.calls += 1
        if self.calls == 1:
            return Scorecard(scores={"x": 0.1}, overall=0.1, details={"reason": "low"})
        return Scorecard(scores={"x": 0.9}, overall=0.9, details={"reason": "high"})


def test_graph_retries(monkeypatch):
    ff.PARALLEL_EXEC_ENABLED = False
    ff.EVALUATORS_ENABLED = True
    monkeypatch.setattr("dr_rd.evaluation.scorecard.evaluate", EvalStub())

    # stub plan -> two tasks? only one needed
    def fake_plan(idea, constraint_text, risk, ui_model=None):
        return [{"id": "t1", "title": "a", "description": "b"}]

    def fake_route(task, ui_model=None):
        return "Role", None, None, {"id": task["id"], "role": "Role", "title": "a", "description": "b"}

    attempt = {"n": 0}

    def fake_dispatch(task, ui_model=None):
        attempt["n"] += 1
        return {"content": f"run {attempt['n']}"}

    def fake_compose(idea, answers):
        return "done"

    monkeypatch.setattr("core.orchestrator.generate_plan", fake_plan)
    monkeypatch.setattr("core.router.route_task", fake_route)
    monkeypatch.setattr("core.router.dispatch", fake_dispatch)
    monkeypatch.setattr("core.orchestrator.compose_final_proposal", fake_compose)

    from core.graph.graph import run_langgraph

    final, answers, bundle = run_langgraph(
        "idea",
        max_retries=1,
        retry_backoff={"base_s": 0.0, "factor": 1.0, "max_s": 0.0},
    )
    assert answers["t1"]["content"] == "run 2"
    attempts = [t for t in bundle["trace"] if t.get("event") == "attempt"]
    assert len(attempts) == 2
