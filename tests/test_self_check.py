import json
from core.evaluation.self_check import validate_and_retry


def test_self_check_retry_success():
    calls = {"count": 0}

    def retry_fn(reminder: str) -> str:
        calls["count"] += 1
        return json.dumps(
            {
                "role": "Research Scientist",
                "task": "t",
                "findings": [],
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        )

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert json.loads(fixed)["role"] == "Research Scientist"
    assert meta == {"retried": True, "valid_json": True}
    assert calls["count"] == 1


def test_self_check_retry_failure():
    def retry_fn(reminder: str) -> str:
        return "still bad"

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert fixed == bad_output
    assert meta == {"retried": True, "valid_json": False}
