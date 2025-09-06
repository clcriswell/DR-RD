from core.evaluation.self_check import validate_and_retry


def test_self_check_escalates_and_places_placeholder():
    def retry(_rem):
        return "{}"  # still invalid

    def escalate(_rem):
        return "{}"  # still invalid

    result, meta = validate_and_retry(
        "Dynamic Specialist",
        {"id": "T1", "title": "t"},
        "{}",
        retry,
        escalate_fn=escalate,
    )
    assert meta.get("escalated") and not meta.get("valid_json")
    assert result["findings"] == "Not determined"
