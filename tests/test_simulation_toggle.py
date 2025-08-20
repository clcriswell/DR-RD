from unittest.mock import patch
import pytest
from core.agents.simulation_agent import SimulationAgent
from simulation.simulation_manager import SimulationManager

@pytest.fixture
def sample_outputs():
    return {
        "Mechanical & Precision-Motion Engineer": "spec1",
        "Photonics Electronics Engineer": "spec2",
        "Chemical & Surface Science Specialist": "spec3",
        "Project Manager / Principal Investigator": "overview",
    }

def test_simulation_toggle(sample_outputs):
    sim_agent = SimulationAgent()
    with patch.object(SimulationManager, 'simulate') as mock_sim:
        simulate_enabled = False
        if simulate_enabled:
            sim_agent.append_simulations(sample_outputs)
        assert mock_sim.call_count == 0
    with patch.object(SimulationManager, 'simulate') as mock_sim:
        simulate_enabled = True
        if simulate_enabled:
            sim_agent.append_simulations(sample_outputs)
        assert mock_sim.call_count == 3

