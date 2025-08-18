from orchestrators.plan_utils import normalize_plan_to_tasks


def test_single_object_wraps():
    raw = {"role": "CTO", "title": "Plan", "description": "Design"}
    tasks = normalize_plan_to_tasks(raw, backfill=False, dedupe=False)
    assert len(tasks) == 1
    assert tasks[0]["role"] == "CTO"


def test_dict_a_ignores_strings():
    raw = {
        "CTO": [{"title": "Do", "description": "Thing"}],
        "Finance": "ignored",
    }
    tasks = normalize_plan_to_tasks(raw, backfill=False, dedupe=False)
    assert len(tasks) == 1
    assert tasks[0]["role"] == "CTO"


def test_array_b_canonicalizes_and_dedupes():
    raw = [
        {"role": "chief technology officer", "title": "a", "description": "b"},
        {"role": "CTO", "title": "a", "description": "b"},
        {"role": "marketing", "title": "m", "description": "d"},
    ]
    tasks = normalize_plan_to_tasks(raw, backfill=False, dedupe=True)
    assert len(tasks) == 2
    roles = {t["role"] for t in tasks}
    assert roles == {"CTO", "Marketing Analyst"}
