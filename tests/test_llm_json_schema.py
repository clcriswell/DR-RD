import json

import jsonschema

from core.agents.base_agent import LLMRoleAgent
from core.agents.materials_engineer_agent import MaterialsEngineerAgent


def test_schema_agent_returns_valid_json(monkeypatch):
    captured = {}

    def fake_act(self, system, user, **kwargs):
        captured["response_format"] = kwargs.get("response_format")
        return json.dumps(
            {
                "role": "Materials Engineer",
                "task": "t",
                "summary": "",
                "findings": "",
                "properties": [
                    {
                        "name": "mat",
                        "property": "prop",
                        "value": 0,
                        "units": "",
                        "source": "",
                    }
                ],
                "tradeoffs": [],
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        )

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act, raising=False)
    agent = MaterialsEngineerAgent("gpt-4o-mini")
    out = agent({"description": "t"}, model="gpt-4o-mini", meta={"context": "idea"})
    data = json.loads(out)
    with open("dr_rd/schemas/materials_engineer_v2.json", encoding="utf-8") as fh:
        schema = json.load(fh)
    jsonschema.validate(data, schema)
    assert captured["response_format"]["type"] == "json_schema"
