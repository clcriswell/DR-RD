import importlib
from pathlib import Path

from tests.audit.fixtures import poc_execution as fixtures


def test_simulation_harness_runs(tmp_path):
    sim_mod = importlib.import_module("simulation.simulation_manager")
    sim = sim_mod.SimulationManager()
    qa = fixtures.DummyQARouter()
    result = sim.simulate("thermal", "spec", qa_router=qa, outputs_dir=tmp_path)
    assert isinstance(result, dict)
    assert qa.called, "qa router not invoked on failure"


def test_failure_routes_back_to_qa(tmp_path):
    sim_mod = importlib.import_module("simulation.simulation_manager")
    sim = sim_mod.SimulationManager()
    qa = fixtures.DummyQARouter()
    sim.simulate("thermal", "spec", qa_router=qa, outputs_dir=tmp_path)
    assert qa.called
    assert qa.context and qa.context.get("sim_type") == "thermal"


def test_artifacts_persisted_under_runs_folder():
    runs = Path("runs")
    outputs = Path("outputs")
    assert any(p.exists() and list(p.glob("*/")) for p in (runs, outputs)), \
        "no timestamped runs/outputs folder present"
