import json
import logging
from collections import deque
from unittest.mock import patch

import config.feature_flags as ff
from core import orchestrator


def test_execute_plan_retry_and_parallel(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: None
    )
    outputs = {
        "Analyst": deque(
            [
                (
                    '{"role":"Analyst","task":"t","findings":[1],'
                    '"risks":[2],"next_steps":[3],"sources":[]}'
                )
            ]
        ),
        "Checker": deque(
            [
                "not json",
                (
                    '{"role":"Checker","task":"t","findings":[1],'
                    '"risks":[2],"next_steps":[3],"sources":[]}'
                ),
            ]
        ),
    }

    def fake_route(task, ui_model=None):
        class Dummy:
            def __init__(self, model):
                self.model = model

        return task["role"], Dummy, "m", task

    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        return outputs[task["role"]].popleft()

    monkeypatch.setattr(orchestrator, "route_task", fake_route)
    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)

    tasks = [
        {"role": "Analyst", "title": "A", "description": "a"},
        {"role": "Checker", "title": "B", "description": "b"},
    ]

    ff.PARALLEL_EXEC_ENABLED = False
    serial = orchestrator.execute_plan("idea", tasks, agents={})

    outputs["Analyst"] = deque(
        [('{"role":"Analyst","task":"t","findings":[1],' '"risks":[2],"next_steps":[3],"sources":[]}')]
    )
    outputs["Checker"] = deque(
        [
            "not json",
                (
                    '{"role":"Checker","task":"t","findings":[1],'
                    '"risks":[2],"next_steps":[3],"sources":[]}'
                ),
        ]
    )
    ff.PARALLEL_EXEC_ENABLED = True
    parallel = orchestrator.execute_plan("idea", tasks, agents={})

    assert serial == parallel
    for text in parallel.values():
        parsed = orchestrator.extract_json_block(text)
        data = parsed if isinstance(parsed, dict) else json.loads(parsed or text)
        assert data["role"] in {"Analyst", "Checker"}


def test_evaluator_hook_called(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: None
    )
    called = {"n": 0}

    def spy(*args, **kwargs):
        called["n"] += 1
        from core.evaluation.self_check import validate_and_retry as real

        return real(*args, **kwargs)

    monkeypatch.setattr(ff, "PARALLEL_EXEC_ENABLED", False)
    monkeypatch.setattr(
        orchestrator,
        "route_task",
        lambda t, ui=None: (t["role"], type("D", (), {"__init__": lambda self, m: None}), "m", t),
    )
    good_json = (
        '{"role":"Analyst","task":"t","findings":[1],' '"risks":[2],"next_steps":[3],"sources":[]}'
    )
    monkeypatch.setattr(orchestrator, "invoke_agent_safely", lambda *a, **k: good_json)
    monkeypatch.setattr(orchestrator, "validate_and_retry", spy)

    orchestrator.execute_plan(
        "idea", [{"role": "Analyst", "title": "T", "description": "d"}], agents={}
    )
    assert called["n"] >= 1


def test_log_marker_and_no_mode(caplog):
    with patch.object(orchestrator, "generate_plan", return_value=[]), patch.object(
        orchestrator, "execute_plan", return_value={}
    ), patch.object(orchestrator, "compose_final_proposal", return_value="x"):
        caplog.set_level(logging.INFO)
        orchestrator.orchestrate("idea")
    markers = [r for r in caplog.records if "UnifiedPipeline:" in r.getMessage()]
    assert len(markers) == 1

    for fn in (
        orchestrator.generate_plan,
        orchestrator.execute_plan,
        orchestrator.compose_final_proposal,
    ):
        assert "mode" not in fn.__code__.co_varnames
