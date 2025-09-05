import json

from core.evaluation.self_check import _has_required, validate_and_retry


def test_self_check_retry_success(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: None
    )
    calls = {"count": 0}

    def retry_fn(reminder: str) -> str:
        calls["count"] += 1
        return json.dumps(
            {
                "role": "Research Scientist",
                "task": "t",
                "findings": ["f"],
                "risks": ["r"],
                "next_steps": ["n"],
                "sources": [],
            }
        )

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert json.loads(fixed)["role"] == "Research Scientist"
    assert meta == {"retried": True, "valid_json": True}
    assert calls["count"] == 1


def test_self_check_retry_failure(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: None
    )

    def retry_fn(reminder: str) -> str:
        return "still bad"

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry(
        "Research Scientist", {"title": "t"}, bad_output, retry_fn
    )
    assert fixed["valid_json"] is False
    assert meta == {"retried": True, "valid_json": False}


def test_self_check_retry_dict_output(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: None
    )
    calls = {"count": 0}

    def retry_fn(reminder: str):
        calls["count"] += 1
        return {
            "role": "Research Scientist",
            "task": "t",
            "findings": ["f"],
            "risks": ["r"],
            "next_steps": ["n"],
            "sources": [],
        }

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert json.loads(fixed)["role"] == "Research Scientist"
    assert meta == {"retried": True, "valid_json": True}
    assert calls["count"] == 1


def test_has_required_rejects_empty_strings():
    data = {
        "role": "r",
        "task": " ",
        "findings": ["x"],
        "risks": ["r"],
        "next_steps": ["n"],
        "sources": [],
    }
    assert _has_required(data) is False


def test_has_required_allows_empty_sources():
    data = {
        "role": "r",
        "task": "t",
        "findings": ["x"],
        "risks": ["r"],
        "next_steps": ["n"],
        "sources": [],
    }
    assert _has_required(data) is True
