import logging

from core.router import ALIASES, choose_agent_for_task, route_task
from core.agents.registry import AGENT_REGISTRY


def test_alias_mapping():
    role, cls = choose_agent_for_task("Manufacturing Technician", "", "")
    assert role == "Research Scientist"
    assert cls is AGENT_REGISTRY[role]


def test_unresolved_role_logs(caplog):
    caplog.set_level(logging.WARNING)
    role, cls = choose_agent_for_task("Unknown Role", "title", "desc")
    assert role == "Research Scientist"
    assert any("Unknown Role" in r.message for r in caplog.records)


def test_stop_rules_propagation():
    task = {"role": "Finance", "title": "Budget", "description": "", "stop_rules": ["halt"]}
    role, cls, routed = route_task(task)
    assert routed["stop_rules"] == ["halt"]
    assert role == routed["role"]
