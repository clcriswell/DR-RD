from core.orchestrator import _normalize_plan_payload


def test_summary_only_backfills_description():
    data = {"tasks": [{"title": "T1", "summary": "sum"}]}
    norm = _normalize_plan_payload(data)
    task = norm["tasks"][0]
    assert task["description"] == "sum"
    assert task["summary"] == "sum"


def test_description_only_backfills_summary():
    data = {"tasks": [{"title": "T1", "description": "desc"}]}
    norm = _normalize_plan_payload(data)
    task = norm["tasks"][0]
    assert task["summary"] == "desc"
    assert task["description"] == "desc"
