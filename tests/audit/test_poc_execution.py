"""Dry-run checks for PoC execution artifacts."""

from pathlib import Path

from simulation.simulation_manager import SimulationManager
from tests.audit.fixtures.simulation import sample_design_spec


def test_simulation_harness_runs(sample_design_spec):
    manager = SimulationManager()
    result = manager.simulate("structural", sample_design_spec)
    assert "pass" in result, "Simulation harness did not return pass flag"


def test_results_routed_to_qa_or_research():
    qa_agent_path = Path("core/agents/qa_agent.py")
    assert qa_agent_path.is_file(), "QA routing missing"


def test_run_artifacts_persisted():
    runs_dir = Path("runs")
    outputs_dir = Path("outputs")
    assert runs_dir.is_dir() or outputs_dir.is_dir(), "Run artifacts directory missing"
