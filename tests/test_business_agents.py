import json
from unittest.mock import Mock, patch
import json
from unittest.mock import Mock, patch

from agents.marketing_agent import MarketingAgent
from agents.ip_analyst_agent import IPAnalystAgent
from core.agents import registry


def _fake_response(payload: dict):
    choice = Mock()
    choice.message = Mock(content=json.dumps(payload))
    choice.usage = Mock(prompt_tokens=1, completion_tokens=1)
    return Mock(choices=[choice])


@patch("agents.marketing_agent.llm_call")
def test_marketing_agent_contract(mock_call):
    mock_call.return_value = _fake_response(
        {
            "role": "Marketing Analyst",
            "task": "Assess market",
            "findings": [],
            "risks": [],
            "next_steps": [],
            "sources": [],
        }
    )
    agent = MarketingAgent("gpt-4o-mini")
    result = agent.act("idea", "study customers")
    assert set(result.keys()) >= {
        "role",
        "task",
        "findings",
        "risks",
        "next_steps",
        "sources",
    }


@patch("agents.ip_analyst_agent.llm_call")
def test_ip_agent_contract(mock_call):
    mock_call.return_value = _fake_response(
        {
            "role": "IP Analyst",
            "task": "Check novelty",
            "findings": [],
            "risks": [],
            "next_steps": [],
            "sources": [],
        }
    )
    agent = IPAnalystAgent("gpt-4o-mini")
    result = agent.act("idea", "scan patents")
    assert set(result.keys()) >= {
        "role",
        "task",
        "findings",
        "risks",
        "next_steps",
        "sources",
    }


def test_router_dispatches_to_new_agents():
    agents = registry.build_agents("test")
    a1, role1 = registry.choose_agent_for_task(
        None, "Analyze competitor pricing and market segments", agents
    )
    assert a1.name == "Marketing Analyst" and role1 == "Marketing Analyst"
    a2, role2 = registry.choose_agent_for_task(
        None, "Review patent claims for novelty", agents
    )
    assert a2.name == "IP Analyst" and role2 == "IP Analyst"
