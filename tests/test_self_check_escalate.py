from core.evaluation.self_check import validate_and_retry


def test_self_check_places_placeholder_after_retry():
    def retry(_rem):
        return "{}"  # still invalid

    result, meta = validate_and_retry(
        "Dynamic Specialist",
        {"id": "T1", "title": "t"},
        "{}",
        retry,
    )
    assert not meta.get("valid_json")
    assert result["findings"] == "Not determined"
