import json
from collections import deque

import config.feature_flags as ff
from core import orchestrator


def test_artifact_written_for_invalid_output(monkeypatch):
    monkeypatch.setattr(ff, "PARALLEL_EXEC_ENABLED", False)

    class DummyAgent:
        def __init__(self, model):
            self.model = model

    monkeypatch.setattr(
        orchestrator,
        "route_task",
        lambda t, ui_model=None: (t["role"], DummyAgent, "m", t),
    )
    monkeypatch.setattr(orchestrator, "pseudonymize_for_model", lambda x: (x, {}))
    monkeypatch.setattr(orchestrator, "select_model", lambda purpose, agent_name=None: "m")
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)

    outputs = deque(["not json", "not json"])  # force placeholder

    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        return outputs.popleft()

    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)

    run_id = "artifact_test"
    tasks = [{"role": "Research Scientist", "title": "T", "description": "d"}]
    orchestrator.execute_plan("idea", tasks, agents={}, run_id=run_id)

    from utils.paths import run_root

    path = run_root(run_id) / "T01_output.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert (
        data.get("error") == "Agent failed to produce output"
        or data.get("findings") == "Not determined"
    )
