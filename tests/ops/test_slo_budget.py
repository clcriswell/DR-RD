from dr_rd.ops import slo


def test_slo_budget_computation():
    events = [
        {"type": "counter", "name": "runs_started", "value": 10, "labels": {}},
        {"type": "counter", "name": "runs_succeeded", "value": 9, "labels": {}},
        {"type": "counter", "name": "runs_failed", "value": 1, "labels": {}},
        {"type": "histogram", "name": "phase_latency_ms", "value": 100, "labels": {"phase": "exec"}},
        {"type": "counter", "name": "citations_missing", "value": 1, "labels": {}},
        {"type": "counter", "name": "schema_validation_failures", "value": 1, "labels": {}},
    ]
    targets = {"slos": {"availability": 99.0}}
    summary = slo.compute_slo(events, targets)
    assert summary["sli_values"]["availability"] == 90.0
    assert "availability" in summary["budget_remaining"]
