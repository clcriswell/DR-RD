from core.sim.summary import summarize_runs


def test_sweep_detection_and_stats():
    runs = [
        {"param": 1, "output": 1},
        {"param": 2, "output": 4},
        {"param": 3, "output": 9},
    ]
    summary = summarize_runs(runs)
    assert summary["sweep_key"] == "param"
    assert summary["mean"] == 14 / 3
    assert summary["downsampled"] is False


def test_monte_carlo_downsample():
    runs = [{"output": i} for i in range(100)]
    summary = summarize_runs(runs, max_points=10)
    assert summary["sweep_key"] is None
    assert summary["downsampled"] is True
    assert len(summary["sampled"]) == 10
    assert summary["p50"] == 49.5
