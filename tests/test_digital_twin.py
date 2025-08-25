from dr_rd.tools.simulations import simulate


def test_single_run_contains_output():
    res = simulate({"x": 1, "y": 2})
    assert "output" in res


def test_sweep_runs_length():
    res = simulate({"sweep": [{"x": 1}, {"x": 2}]})
    assert len(res["runs"]) == 2


def test_monte_carlo_summary():
    res = simulate({"x": 1, "monte_carlo": 5, "seed": 42})
    assert len(res["runs"]) == 5
    assert "mean_output" in res
