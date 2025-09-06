import json
import logging
from collections import deque

import config.feature_flags as ff
from core import orchestrator


def _setup(monkeypatch, outputs):
    monkeypatch.setattr(ff, "PARALLEL_EXEC_ENABLED", False)
    monkeypatch.setattr(ff, "REFLECTION_ENABLED", False)

    class DummyAgent:
        def __init__(self, model):
            self.model = model

    monkeypatch.setattr(
        orchestrator,
        "route_task",
        lambda t, ui_model=None: (t["role"], DummyAgent, "m", t),
    )
    monkeypatch.setattr(orchestrator, "pseudonymize_for_model", lambda x: (x, {}))
    monkeypatch.setattr(
        orchestrator,
        "select_model",
        lambda purpose, ui_model=None, agent_name=None: "m-high" if purpose == "agent_high" else "m",
    )
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)

    call_outputs = deque(outputs)

    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        return call_outputs.popleft()

    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)
    return call_outputs


def test_retry_ladder_escalates_and_accepts(monkeypatch, caplog):
    outputs = [
        "bad",
        "bad",
        json.dumps(
            {
                "role": "Research Scientist",
                "task": "t",
                "findings": ["ok"],
                "risks": ["r"],
                "next_steps": ["n"],
                "sources": ["s"],
            }
        ),
    ]
    _setup(monkeypatch, outputs)
    caplog.set_level(logging.INFO)
    answers = orchestrator.execute_plan(
        "idea", [{"role": "Research Scientist", "title": "T", "description": "d"}], agents={}
    )
    parsed = json.loads(answers["Research Scientist"])
    assert parsed["findings"] == ["ok"]


def test_retry_ladder_emits_placeholder(monkeypatch, caplog):
    outputs = ["bad", "bad", "bad", "bad"]
    _setup(monkeypatch, outputs)
    caplog.set_level(logging.INFO)
    answers = orchestrator.execute_plan(
        "idea", [{"role": "Research Scientist", "title": "T", "description": "d"}], agents={}
    )
    parsed = json.loads(answers["Research Scientist"])
    assert parsed["findings"] == "Not determined"

    # E2E synth step consumes placeholder without crashing
    monkeypatch.setattr(
        orchestrator, "complete", lambda *a, **k: type("R", (), {"content": "ok"})()
    )
    final = orchestrator.compose_final_proposal("idea", answers)
    assert final.startswith("ok")
