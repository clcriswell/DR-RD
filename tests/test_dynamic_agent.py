import json

import pytest

from core import tool_router
from core.llm import ChatResult
from dr_rd.agents.dynamic_agent import DynamicAgent


def test_dynamic_agent(monkeypatch):
    output = {"role": "Tmp", "task": "t", "result": {}, "sources": []}

    def fake_complete(system, user, model=None, **kwargs):
        return ChatResult(content=json.dumps(output), raw=output)

    monkeypatch.setattr("dr_rd.agents.dynamic_agent.complete", fake_complete)
    agent = DynamicAgent("gpt")
    spec = {
        "role_name": "Tmp",
        "task_brief": "t",
        "schema_draft": {
            "type": "object",
            "properties": {"x": {"type": "number"}},
            "required": ["x"],
        },
        "tool_allowlist": ["lookup_materials"],
    }
    data, schema = agent.run(spec)
    assert "$schema" in schema
    with pytest.raises(PermissionError):
        tool_router.call_tool("Tmp", "npv", {"cash_flows": [1.0], "discount_rate": 0.1})
    tool_router.call_tool("Tmp", "lookup_materials", {"query": "steel"})
