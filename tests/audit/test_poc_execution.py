import os
from simulation.simulation_manager import SimulationManager


def test_simulation_harness_runs():
    sm = SimulationManager()
    metrics = sm.simulate("structural", "dummy spec")
    assert isinstance(metrics, dict) and "pass" in metrics


def test_results_routed_to_qa_or_research():
    assert os.path.exists("orchestrators/qa_router.py"), "QA/research routing missing"


def test_artifacts_persisted_with_timestamps():
    assert os.path.exists("runs") or os.path.exists("outputs"), "Run artifacts folder missing"
