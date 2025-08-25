import logging
from core.router import choose_agent_for_task


def test_synonym_mapping():
    role, _, _ = choose_agent_for_task("Project Manager", "", "")
    assert role == "Planner"
    role, _, _ = choose_agent_for_task("Risk Manager", "", "")
    assert role == "Regulatory"


def test_fallback_to_research_scientist(caplog):
    caplog.set_level(logging.INFO)
    role, _, _ = choose_agent_for_task("Unknown", "", "")
    assert role == "Research Scientist"
    assert any("Fallback routing" in r.message for r in caplog.records)


def test_keyword_expansion():
    assert choose_agent_for_task(None, "Quantum computing", "")[0] == "Research Scientist"
    assert choose_agent_for_task(None, "", "materials selection")[0] == "Materials Engineer"
    assert choose_agent_for_task(None, "", "hiring plan")[0] == "HRM"
    assert choose_agent_for_task(None, "QA review", "")[0] == "Reflection"
