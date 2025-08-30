import json

from core.agents import base_agent, planner_agent
from memory.memory_manager import MemoryManager
from utils.search_tools import obfuscate_query


def test_redaction_masks_pii_and_idea_tokens():
    idea = "Design SuperBattery 3000 for ACME Motors; ceo@acme.com"
    q = "best suppliers for Superbattery 3000 at https://example.com"
    red = obfuscate_query("Researcher", idea, q)
    assert "[REDACTED_EMAIL]" in red
    assert "[REDACTED_URL]" in red
    assert "SuperBattery" not in red
    assert "3000" not in red


def test_planner_accepts_constraints_and_risk(monkeypatch):
    def fake_complete(system_prompt, user_prompt, **kwargs):
        class Resp:
            content = json.dumps({"tasks": []})

        return Resp()

    monkeypatch.setattr(base_agent, "complete", fake_complete)
    agent = planner_agent.PlannerAgent("gpt-4o-mini")
    result = agent.run("Build battery", "", constraints="No cobalt", risk_posture="Low")
    assert json.loads(result)["tasks"] == []


def test_memory_persists_new_fields(tmp_path):
    file = tmp_path / "mem.json"
    mm = MemoryManager(file_path=str(file))
    mm.store_project(
        "Test",
        "Idea",
        [],
        {},
        "Proposal",
        constraints="C",
        risk_posture="High",
    )
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    assert data[-1]["constraints"] == "C"
    assert data[-1]["risk_posture"] == "High"


def test_scope_note_normalization(monkeypatch):
    import types

    import core.orchestrator as orch

    def fake_complete(system, user_prompt):
        class R:
            content = '{"tasks":[]}'

        return R()

    monkeypatch.setattr(orch, "complete", fake_complete)
    monkeypatch.setattr(orch, "st", types.SimpleNamespace(session_state={}))

    orch.generate_plan("Build", "C1\nC2", risk_posture="HIGH")
    scope = orch.st.session_state["scope_note"]
    assert scope["constraints"] == ["C1", "C2"]
    assert scope["risk_posture"] == "high"
