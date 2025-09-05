import json
from core import orchestrator
from core.orchestrator import execute_plan

class DummyAgent:
    def __init__(self, model):
        self.model = model
    def run(self, spec):
        # return minimal valid JSON
        return {
            "role": "Dynamic Specialist",
            "task": spec.get("task_brief", ""),
            "findings": "ok",
            "risks": [],
            "next_steps": [],
            "sources": [],
        }

def test_dynamic_agent_spec_construction(monkeypatch):
    captured = {}
    def fake_invoke(agent, task, model=None, meta=None, run_id=None):
        captured.update(task)
        return agent.run(task)
    monkeypatch.setattr(orchestrator, "invoke_agent_safely", fake_invoke)
    agents = {"Dynamic Specialist": DummyAgent("m")}
    tasks = [{"id": "T1", "title": "Title", "description": "Desc", "role": "Dynamic Specialist"}]
    execute_plan("idea", tasks, agents=agents, run_id="r")
    assert captured["role_name"] == "Dynamic Specialist"
    assert "task_brief" in captured and captured["task_brief"].startswith("Title")
    assert captured["io_schema_ref"] == "dr_rd/schemas/generic_v1.json"
