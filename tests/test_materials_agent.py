import json

from core import tool_router
from core.agents.materials_agent import MaterialsAgent
from core.llm import ChatResult


def test_materials_agent(monkeypatch):
    call_count = {"n": 0}
    valid = {
        "role": "Materials",
        "task": "check",
        "summary": "ok",
        "properties": [
            {
                "name": "Aluminum",
                "property": "tensile_strength",
                "value": 310,
                "units": "MPa",
                "source": "sample",
            }
        ],
        "tradeoffs": [],
        "risks": [],
        "next_steps": [],
        "sources": ["sample"],
    }

    def fake_complete(system, user, model=None, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return ChatResult(content="{}", raw={})
        return ChatResult(content=json.dumps(valid), raw={})

    monkeypatch.setattr("core.agents.materials_agent.complete", fake_complete)
    agent = MaterialsAgent("gpt")
    res = agent.run("check", "Aluminum")
    assert res["role"] == "Materials"
    assert call_count["n"] == 2
    prov = tool_router.get_provenance()
    assert any(p["tool"] == "lookup_materials" for p in prov)
