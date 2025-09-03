from core.orchestrator import _coerce_and_fill


def test_summary_only_backfills_description_and_role():
    data = {"tasks": [{"title": "T1", "summary": "sum"}]}
    norm = _coerce_and_fill(data)
    task = norm["tasks"][0]
    assert task["description"] == "sum"
    assert task["role"] == "Dynamic Specialist"


def test_description_only_backfills_summary():
    data = {"tasks": [{"title": "T1", "description": "desc"}]}
    norm = _coerce_and_fill(data)
    task = norm["tasks"][0]
    assert task["summary"] == "desc"
    assert task["description"] == "desc"
