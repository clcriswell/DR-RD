import json
from unittest.mock import Mock, patch
import json

from core.llm import ChatResult

from core.agents.marketing_agent import MarketingAgent
from core.agents.ip_analyst_agent import IPAnalystAgent
from core.router import choose_agent_for_task


def _fake_response(payload: dict):
    raw = Mock()
    raw.usage = Mock(prompt_tokens=1, completion_tokens=1)
    return ChatResult(content=json.dumps(payload), raw=raw)


@patch("core.agents.base_agent.complete")
def test_marketing_agent_contract(mock_call):
    mock_call.return_value = _fake_response(
        {
            "role": "Marketing Analyst",
            "task": "Assess market",
            "summary": "ok",
            "findings": [],
            "risks": [],
            "next_steps": [],
            "sources": [],
        }
    )
    agent = MarketingAgent("gpt-5")
    result = json.loads(agent.act("idea", "study customers"))
    assert set(result.keys()) >= {
        "role",
        "task",
        "summary",
        "findings",
        "risks",
        "next_steps",
        "sources",
    }


@patch("core.agents.base_agent.complete")
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
    agent = IPAnalystAgent("gpt-5")
    result = json.loads(agent.act("idea", "scan patents"))
    assert set(result.keys()) >= {
        "role",
        "task",
        "findings",
        "risks",
        "next_steps",
        "sources",
    }


def test_router_dispatches_to_new_agents():
    role1, cls1, _ = choose_agent_for_task(
        "Marketing", "Analyze competitor pricing and market segments", "", None, task={}
    )
    assert cls1.__name__ == "MarketingAgent" and role1 == "Marketing Analyst"
    role2, cls2, _ = choose_agent_for_task(
        "IP Analyst", "Review patent claims for novelty", "", None, task={}
    )
    assert cls2.__name__ == "IPAnalystAgent" and role2 == "IP Analyst"
