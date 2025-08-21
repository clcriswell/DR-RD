import json

from memory.memory_manager import MemoryManager
from utils.search_tools import obfuscate_query
from core.agents import planner_agent


def test_redaction_masks_pii_and_idea_tokens():
    idea = "Design SuperBattery 3000 for ACME Motors; ceo@acme.com"
    q = "best suppliers for Superbattery 3000 at https://example.com"
    red = obfuscate_query("Researcher", idea, q)
    assert "[REDACTED_EMAIL]" in red
    assert "[REDACTED_URL]" in red
    assert "SuperBattery" not in red
    assert "3000" not in red


def test_planner_prompt_includes_constraints_and_risk(monkeypatch):
    captured = {}

    def fake_llm_call(_logger, model, stage, messages, **kwargs):
        captured["messages"] = messages
        # Minimal object with JSON content
        class Resp:
            choices = [
                type(
                    "obj",
                    (),
                    {
                        "message": type("obj2", (), {"content": json.dumps({"tasks": []})})(),
                        "finish_reason": "stop",
                        "usage": type("U", (), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})(),
                    },
                )
            ]

        return Resp()

    monkeypatch.setattr(planner_agent, "llm_call", fake_llm_call)
    agent = planner_agent.PlannerAgent()
    agent.run("Build battery", "", constraints="No cobalt", risk_posture="Low")
    user_msg = [m for m in captured["messages"] if m["role"] == "user"][0]["content"]
    assert "Constraints: No cobalt" in user_msg
    assert "Risk posture: Low" in user_msg


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
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data[-1]["constraints"] == "C"
    assert data[-1]["risk_posture"] == "High"


def test_scope_note_normalization(monkeypatch):
    import types
    import core.orchestrator as orch

    def fake_complete(system, user_prompt):
        class R:
            content = "{\"tasks\":[]}"

        return R()

    monkeypatch.setattr(orch, "complete", fake_complete)
    monkeypatch.setattr(orch, "st", types.SimpleNamespace(session_state={}))

    orch.generate_plan("Build", "C1\nC2", risk_posture="HIGH")
    scope = orch.st.session_state["scope_note"]
    assert scope["constraints"] == ["C1", "C2"]
    assert scope["risk_posture"] == "high"

