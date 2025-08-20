import pytest
from core.agents.simulation_agent import determine_sim_type


@pytest.mark.parametrize(
    "role,spec,expected",
    [
        ("Mechanical & Precision-Motion Engineer", "spec", "structural"),
        ("Photonics Electronics Engineer", "spec", "electronics"),
        ("Chemical & Surface Science Specialist", "spec", "chemical"),
        ("Project Manager", "This device needs thermal dissipation.", "thermal"),
        ("Project Manager", "spec", ""),
    ],
)
def test_determine_sim_type(role, spec, expected):
    assert determine_sim_type(role, spec) == expected
