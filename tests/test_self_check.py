import json

from core.evaluation.self_check import _has_required, validate_and_retry


def test_self_check_retry_success(monkeypatch):
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)
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
    assert meta == {"retried": True, "valid_json": True, "missing_keys": []}
    assert calls["count"] == 1


def test_self_check_retry_failure(monkeypatch):
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)

    def retry_fn(reminder: str) -> str:
        return "still bad"

    bad_output = "No JSON here"
    fixed, meta = validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert fixed["findings"] == "Not determined"
    assert meta == {"retried": True, "valid_json": False, "missing_keys": []}


def test_self_check_retry_dict_output(monkeypatch):
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)
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
    assert meta == {"retried": True, "valid_json": True, "missing_keys": []}
    assert calls["count"] == 1


def test_missing_keys_reminder(monkeypatch):
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
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

    bad_output = json.dumps({"role": "Research Scientist", "task": "t"})
    validate_and_retry("Research Scientist", {"title": "t"}, bad_output, retry_fn)
    assert captured["reminder"].startswith("Reminder:")
    for key in ["findings", "risks", "next_steps", "sources"]:
        assert f"missing '{key}'" in captured["reminder"]


def test_schema_missing_multiple_keys(monkeypatch):
    schema = {
        "type": "object",
        "properties": {
            "total_cost": {"type": "number"},
            "contribution_margin": {"type": "number"},
        },
        "required": ["total_cost", "contribution_margin"],
    }
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: schema)
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        return json.dumps(
            {
                "role": "Finance",
                "task": "t",
                "findings": ["f"],
                "risks": ["r"],
                "next_steps": ["n"],
                "sources": [],
                "total_cost": 1,
                "contribution_margin": 2,
            }
        )

    bad_output = json.dumps(
        {
            "role": "Finance",
            "task": "t",
            "findings": ["f"],
            "risks": ["r"],
            "next_steps": ["n"],
            "sources": [],
        }
    )
    validate_and_retry("Finance", {"title": "t"}, bad_output, retry_fn)
    assert captured["reminder"].startswith("Reminder:")
    assert "missing 'total_cost'" in captured["reminder"]
    assert "missing 'contribution_margin'" in captured["reminder"]


def test_schema_type_mismatch(monkeypatch):
    schema = {
        "type": "object",
        "properties": {"npv": {"type": "number"}, "risks": {"type": "array"}},
        "required": ["npv", "risks"],
    }
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: schema)
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        return json.dumps(
            {
                "role": "Finance",
                "task": "t",
                "findings": ["f"],
                "risks": ["r"],
                "next_steps": ["n"],
                "sources": [],
                "npv": 1,
            }
        )

    bad_output = json.dumps(
        {
            "role": "Finance",
            "task": "t",
            "findings": ["f"],
            "risks": "bad",
            "next_steps": ["n"],
            "sources": [],
            "npv": "Not determined",
        }
    )
    validate_and_retry("Finance", {"title": "t"}, bad_output, retry_fn)
    assert captured["reminder"].startswith("Reminder:")
    assert "used 'Not determined' for a numeric field" in captured["reminder"]
    assert "used a string where an array was required" in captured["reminder"]


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
