import os
from unittest.mock import Mock, patch

from core.agents.planner_agent import PlannerAgent
from core.roles import canonical_roles
from orchestrators.plan_utils import normalize_plan_to_tasks


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


ALLOWED_ROLES = canonical_roles()


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.agents.planner_agent.llm_call")
def test_planner_smoke(mock_llm):
    mock_llm.return_value = make_openai_response(
        '{"tasks": [{"id": "T01", "title": "Do X", "description": "desc", "role": "CTO"}]}'
    )
    agent = PlannerAgent("gpt-5")
    raw = agent.run("idea", "plan")
    tasks = normalize_plan_to_tasks(raw)
    assert len(tasks) >= 6
    assert {t["role"] for t in tasks}.issubset(ALLOWED_ROLES)
