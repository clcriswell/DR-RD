import json

from core import orchestrator, router


def test_reflection_adds_followups(monkeypatch):
    # Enable reflection
    import config.feature_flags as ff

    monkeypatch.setattr(ff, "REFLECTION_ENABLED", True)

    class Dummy:
        def __init__(self, model):
            self.model = model

    registry = {"Research Scientist": Dummy, "Reflection": Dummy, "HRM": Dummy}
    monkeypatch.setattr(router, "AGENT_REGISTRY", registry)
    monkeypatch.setattr(orchestrator, "AGENT_REGISTRY", registry)
    monkeypatch.setattr(router, "select_model", lambda purpose, ui_model, agent_name=None: "m")
    monkeypatch.setattr(orchestrator, "select_model", lambda *a, **k: "m")

    def fake_invoke(agent, idea, task, model=None):
        role = task.get("role")
        if role == "Research Scientist":
            return json.dumps(
                {
                    "role": "Research Scientist",
                    "task": task.get("title"),
                    "findings": [],
                    "risks": [],
                    "next_steps": [],
                    "sources": [],
                }
            )
        if role == "Reflection":
            return json.dumps(["[HRM]: assess hiring needs"])
        if role == "HRM":
            return json.dumps(
                {
                    "role": "HRM",
                    "task": task.get("title"),
                    "findings": [],
                    "risks": [],
                    "next_steps": [],
                    "sources": [],
                }
            )
        return "{}"

    monkeypatch.setattr(orchestrator, "_invoke_agent", fake_invoke)

    tasks = [{"role": "Research Scientist", "title": "Initial", "description": ""}]
    out = orchestrator.execute_plan(
        "idea", tasks, agents={}, save_evidence=False, save_decision_log=False
    )
    assert "Research Scientist" in out
    assert "HRM" in out
