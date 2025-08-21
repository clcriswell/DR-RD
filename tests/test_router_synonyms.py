import logging
from core.router import choose_agent_for_task


def test_synonym_mapping():
    role, _, _ = choose_agent_for_task("Project Manager", "", "")
    assert role == "Planner"
    role, _, _ = choose_agent_for_task("Risk Manager", "", "")
    assert role == "Regulatory"


def test_fallback_to_synthesizer(caplog):
    caplog.set_level(logging.INFO)
    role, _, _ = choose_agent_for_task("Unknown", "", "")
    assert role == "Synthesizer"
    assert any("Fallback routing" in r.message for r in caplog.records)
