from pathlib import Path
import inspect
from simulation.simulation_manager import SimulationManager


def test_poc_test_plan_template_sections():
    content = Path("docs/poc_test_plan.md").read_text()
    for section in ("Hypotheses", "Scenarios", "Metrics", "Gates"):
        assert section in content


def test_simulation_manager_has_hooks():
    sig = inspect.signature(SimulationManager.simulate)
    assert "hooks" in sig.parameters


def test_environment_matrix_defined():
    assert Path("docs/environment_matrix.yaml").exists()
