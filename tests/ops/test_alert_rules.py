from dr_rd.ops import alerts


def test_alert_rules_breach():
    summary = {
        "sli_values": {"availability": 90.0},
        "budget_remaining": {"availability": {"target": 99.0, "remaining": -9.0}},
    }
    report = alerts.evaluate(summary, {"availability": 99.0})
    assert report["breaches"]
    assert report["breaches"][0]["sli"] == "availability"
