import json

from core.agents.planner_agent import PlannerAgent
from dr_rd.prompting.prompt_factory import PromptFactory


def test_planner_returns_tasks(monkeypatch):
    fake = {
        "tasks": [
            {"id": "T01", "title": "t1", "summary": "s", "description": "d", "role": "CTO"},
            {"id": "T02", "title": "t2", "summary": "s", "description": "d", "role": "Materials Engineer"},
            {"id": "T03", "title": "t3", "summary": "s", "description": "d", "role": "Regulatory"},
            {"id": "T04", "title": "t4", "summary": "s", "description": "d", "role": "Finance"},
            {"id": "T05", "title": "t5", "summary": "s", "description": "d", "role": "Marketing Analyst"},
            {"id": "T06", "title": "t6", "summary": "s", "description": "d", "role": "QA"},
        ]
    }
    monkeypatch.setattr(
        "core.agents.base_agent.LLMRoleAgent.act",
        lambda self, sys, user, **_: json.dumps(fake),
    )
    monkeypatch.setattr(
        PromptFactory,
        "build_prompt",
        lambda self, spec: {
            "system": "s",
            "user": "u",
            "io_schema_ref": "",
            "retrieval_plan": {},
            "llm_hints": {},
            "evaluation_hooks": [],
        },
    )
    agent = PlannerAgent("gpt")
    res = agent.run("idea", "")
    data = json.loads(res)
    assert len(data["tasks"]) >= 6
    allowed = {"CTO", "Materials Engineer", "Regulatory", "Finance", "Marketing Analyst", "QA"}
    assert set(t["role"] for t in data["tasks"]) <= allowed
