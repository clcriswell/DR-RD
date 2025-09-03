import logging
from core.router import choose_agent_for_task


def test_synonym_mapping():
    role, _, _ = choose_agent_for_task("Project Manager", "", "", None)
    assert role == "Planner"
    role, _, _ = choose_agent_for_task("Risk Manager", "", "", None)
    assert role == "Regulatory"


def test_fallback_dynamic_specialist():
    role, _, _ = choose_agent_for_task("Unknown", "", "", None)
    assert role == "Dynamic Specialist"


def test_keyword_expansion():
    assert (
        choose_agent_for_task(None, "Quantum computing", "", None)[0] == "Research Scientist"
    )
    assert (
        choose_agent_for_task(None, "", "materials selection", None)[0]
        == "Materials Engineer"
    )
    assert (
        choose_agent_for_task(None, "", "hiring plan", None)[0] == "HRM"
    )
    assert (
        choose_agent_for_task(None, "QA review", "", None)[0] == "QA"
    )
