from core.router import choose_agent_for_task
from core.agents.unified_registry import AGENT_REGISTRY
import dr_rd  # noqa: F401  # ensure role aliases are patched


def _check(role, expected):
    resolved, cls, _model = choose_agent_for_task(role, "t", "d", None)
    assert resolved == expected
    assert resolved in AGENT_REGISTRY
    assert cls is not AGENT_REGISTRY["Synthesizer"]


def test_mechanical_engineer_maps():
    _check("Mechanical Engineer", "Mechanical Systems Lead")


def test_software_engineer_maps():
    _check("Software Engineer", "CTO")


def test_ux_designer_maps():
    _check("UX/UI Designer", "Marketing Analyst")


def test_finance_specialist_maps_to_finance():
    resolved, cls, _model = choose_agent_for_task("Finance Specialist", "t", "d", None)
    assert resolved == "Finance"
    assert cls is AGENT_REGISTRY["Finance"]
