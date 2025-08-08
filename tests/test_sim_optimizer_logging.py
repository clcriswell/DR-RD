import logging

from dr_rd.simulation.design_space import DesignSpace
from dr_rd.simulation.optimizer import optimize


def test_optimizer_logs_best_trial(caplog):
    space = DesignSpace({"x": [0, 1, 2]})

    def simulator(d):
        return {"score": d["x"]}

    def objective(d, metrics):
        return metrics["score"]

    with caplog.at_level(logging.INFO, logger="dr_rd.simulation.optimizer"):
        best_design, _ = optimize({}, space, objective, simulator, strategy="grid")

    assert best_design["x"] == 2
    logs = caplog.text
    assert "best" in logs
    assert "idx=3" in logs
