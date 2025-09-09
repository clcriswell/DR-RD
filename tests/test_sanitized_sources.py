import json
import jsonschema
from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.agents.prompt_agent import PromptFactoryAgent


def _run(role: str, schema_path: str, raw: str, monkeypatch) -> str:
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)

    def fake_act(self, system, user, response_format=None, **kwargs):  # type: ignore[override]
        return raw

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    agent = PromptFactoryAgent("gpt-4o-mini")
    spec = {"role": role, "inputs": {"idea": "", "task": ""}, "io_schema_ref": schema_path}
    return agent.run_with_spec(spec)


def test_finance_drops_invalid_sources(monkeypatch):
    raw = json.dumps(
        {
            "role": "Finance",
            "task": "T1",
            "summary": "",
            "findings": "",
            "unit_economics": {
                "total_revenue": 0,
                "total_cost": 0,
                "gross_margin": 0,
                "contribution_margin": 0,
            },
            "npv": 0,
            "simulations": {"mean": 0, "std_dev": 0, "p5": 0, "p95": 0},
            "assumptions": [],
            "risks": [],
            "next_steps": [],
            "sources": ["valid_source", {}],
        }
    )
    result = _run("Finance", "dr_rd/schemas/finance_v2.json", raw, monkeypatch)
    data = json.loads(result)
    schema = json.load(open("dr_rd/schemas/finance_v2.json", encoding="utf-8"))
    jsonschema.validate(data, schema)
    assert data["sources"] == ["valid_source"]


def test_marketing_converts_dict_sources(monkeypatch):
    raw = json.dumps(
        {
            "role": "Marketing Analyst",
            "task": "T1",
            "summary": "",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": [{"url": "https://abc.com"}],
        }
    )
    result = _run(
        "Marketing Analyst", "dr_rd/schemas/marketing_v2.json", raw, monkeypatch
    )
    data = json.loads(result)
    schema = json.load(open("dr_rd/schemas/marketing_v2.json", encoding="utf-8"))
    jsonschema.validate(data, schema)
    assert data["sources"] == ["https://abc.com"]
