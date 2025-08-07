import importlib
from unittest.mock import patch


def test_optimizer_finds_best(monkeypatch):
    monkeypatch.setenv("SIM_OPTIMIZER_ENABLED", "true")
    monkeypatch.setenv("SIM_OPTIMIZER_STRATEGY", "grid")
    monkeypatch.setenv("SIM_OPTIMIZER_MAX_EVALS", "10")

    # Reload config and agent to pick up env vars
    import config.feature_flags as ff
    import agents.simulation_agent as sa
    import dr_rd.simulation.design_space as ds
    importlib.reload(ff)
    importlib.reload(sa)

    SimulationAgent = sa.SimulationAgent
    DesignSpace = ds.DesignSpace
    sim_agent = SimulationAgent()

    def fake_simulate(sim_type, design_spec):
        # design_spec is formatted like 'x=VALUE'
        val = int(design_spec.split("=")[1])
        return {"score": val}

    space = DesignSpace({"x": [0, 5, 10]})

    def objective(design, metrics):
        # best when score is closest to 5
        return -abs(5 - metrics["score"])

    with patch.object(sa.SimulationManager, "simulate", side_effect=fake_simulate) as mock_sim:
        result = sim_agent.run_simulation(
            "Mechanical Engineer", "x={x}", design_space=space, objective_fn=objective
        )
        assert "- **score**: 5" in result
        assert mock_sim.call_count == 3

