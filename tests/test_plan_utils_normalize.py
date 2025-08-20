from core.plan_utils import normalize_plan_to_tasks, normalize_tasks


def test_single_object_wraps():
    raw = {"role": "CTO", "title": "Plan", "description": "Design"}
    tasks = normalize_plan_to_tasks(raw)
    assert len(tasks) == 1
    assert tasks[0]["role"] == "CTO"


def test_dict_a_ignores_strings():
    raw = {
        "CTO": [{"title": "Doing", "description": "Things"}],
        "Finance": "ignored",
    }
    tasks = normalize_plan_to_tasks(raw)
    assert len(tasks) == 1
    assert tasks[0]["role"] == "CTO"


def test_array_b_canonicalizes_and_dedupes():
    raw = [
        {"role": "chief technology officer", "title": "alpha", "description": "beta"},
        {"role": "CTO", "title": "alpha", "description": "beta"},
        {"role": "marketing", "title": "market", "description": "delta"},
    ]
    tasks = normalize_plan_to_tasks(raw)
    tasks = normalize_tasks(tasks)
    assert len(tasks) == 2
    roles = {t["role"] for t in tasks}
    assert roles == {"CTO", "Marketing Analyst"}
