from core.diagnostics import load_rules, evaluate_diff


def test_diagnostics_rules():
    rules = load_rules()
    diff = {"latency_delta_ms_total": 600, "tool_failure_rate": {"delta": 0.06}}
    result = evaluate_diff(diff, rules)
    assert result["severity"] == "warn"

    diff = {"latency_delta_ms_total": 1300, "tool_failure_rate": {"delta": 0.2}}
    result = evaluate_diff(diff, rules)
    assert result["severity"] == "fail"
