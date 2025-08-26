import json
from core.agents.base_agent import LLMRoleAgent
from core.agents.cto_agent import CTOAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core import tool_router


def _fake_act(self, system_prompt, user_prompt, **kwargs):
    return json.dumps({
        "role": "x",
        "task": "",
        "findings": "",
        "risks": "",
        "next_steps": "",
        "sources": []
    })


def test_agent_calls_tool(monkeypatch):
    called = {}

    def fake_call(agent, tool, params):
        called["tool"] = tool
        return {"ok": True}

    monkeypatch.setattr(tool_router, "call_tool", fake_call)
    monkeypatch.setattr(LLMRoleAgent, "act", _fake_act, raising=False)

    agent = CTOAgent("gpt")
    task = {
        "title": "t",
        "description": "d",
        "tool_request": {"tool": "read_repo", "params": {"globs": ["*.py"]}},
    }
    output = agent.act("idea", task)
    data = json.loads(output)
    assert called["tool"] == "read_repo"
    assert data["tool_result"]["output"] == {"ok": True}


def test_agent_handles_disabled_tool(monkeypatch):
    def fake_call(agent, tool, params):
        raise ValueError("Tool read_repo disabled")

    monkeypatch.setattr(tool_router, "call_tool", fake_call)
    monkeypatch.setattr(LLMRoleAgent, "act", _fake_act, raising=False)

    agent = ResearchScientistAgent("gpt")
    task = {
        "title": "t",
        "description": "d",
        "tool_request": {"tool": "read_repo", "params": {"globs": ["*.py"]}},
    }
    output = agent.act("idea", task)
    data = json.loads(output)
    assert "error" in data["tool_result"]
