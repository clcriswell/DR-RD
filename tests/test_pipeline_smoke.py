import json

from orchestrators.executor import execute
from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.base_agent import LLMRoleAgent
from config import feature_flags


class DummyAgent(PromptFactoryAgent):
    pass


SCHEMAS = {
    "CTO": "dr_rd/schemas/marketing_v2.json",
    "Marketing Analyst": "dr_rd/schemas/marketing_v2.json",
    "Research Scientist": "dr_rd/schemas/marketing_v2.json",
    "Regulatory": "dr_rd/schemas/marketing_v2.json",
    "Finance": "dr_rd/schemas/marketing_v2.json",
    "IP Analyst": "dr_rd/schemas/marketing_v2.json",
}


def test_pipeline_smoke(monkeypatch):
    feature_flags.EVALUATORS_ENABLED = False
    roles = list(SCHEMAS)
    outputs = iter([
        "not json",
        '{"role":"CTO","task":"t","summary":"Feasibility ok.","findings":"","risks":[],"next_steps":"","sources":[]}',
        '{"role":"Marketing Analyst","task":"t","summary":"Market analysis could not be fully completed due to limited data","findings":"","risks":[],"next_steps":"","sources":[],}',
        '{"role":"Research Scientist","task":"t","summary":"rs","findings":"","risks":[],"next_steps":"","sources":[]}',
        '{"role":"Regulatory","task":"t","summary":"reg","findings":"","risks":[],"next_steps":"","sources":[]}',
        '{"role":"Finance","task":"t","summary":"fin","findings":"","risks":[],"next_steps":"","sources":[]}',
        '{"role":"IP Analyst","task":"t","summary":"ip","findings":"","risks":[],"next_steps":"","sources":[]}',
    ])

    def fake_act(self, system, user, **kwargs):  # type: ignore[override]
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)

    def auto_fix(raw):
        if raw == "not json":
            return False, raw
        from utils.json_fixers import attempt_auto_fix as real

        return real(raw)

    monkeypatch.setattr("core.agents.prompt_agent.attempt_auto_fix", auto_fix)

    agent = DummyAgent("gpt-4o-mini")
    findings = {}
    plan = []
    for idx, role in enumerate(roles):
        spec = {
            "role": role,
            "task": "t",
            "inputs": {"idea": "i", "task": "t"},
            "io_schema_ref": SCHEMAS[role],
        }
        res = agent.run_with_spec(spec)
        data = json.loads(res)
        findings[role] = data
        plan.append({"id": str(idx), "role": role, "title": role})
        assert data["summary"] and data["summary"].lower() != "not determined"

    paths = execute(plan, {"run_id": "smoke", "idea": "i", "role_to_findings": findings})
    wp = paths["work_plan"]
    text = wp.read_text()
    assert "(Agent failed to return content)" not in text
    assert "Not determined" not in text
