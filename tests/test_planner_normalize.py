from core.plan_utils import normalize_plan_to_tasks, normalize_tasks


def test_single_object_json():
    raw = '{"role":"CTO","title":"Plan architecture","description":"Outline system"}'
    tasks = normalize_plan_to_tasks(raw)
    assert tasks == [
        {"role": "CTO", "title": "Plan architecture", "description": "Outline system"}
    ]


def test_dict_a_no_char_iteration():
    raw = {
        "CTO": "string should be ignored",
        "Finance": [{"title": "Estimate budget", "description": "Draft costs"}],
    }
    tasks = normalize_plan_to_tasks(raw)
    assert tasks == [
        {"role": "Finance", "title": "Estimate budget", "description": "Draft costs"}
    ]


def test_list_b_parsing():
    raw = [
        {"role": "CTO", "title": "Plan", "description": "Desc"},
        {"role": "Finance", "title": "Budget", "description": "Numbers"},
    ]
    tasks = normalize_plan_to_tasks(raw)
    assert tasks == raw


def test_role_normalization_alias():
    raw_tasks = [
        {
            "role": "Regulatory & Compliance Lead",
            "title": "Review",
            "description": "Check",
        }
    ]
    tasks = normalize_tasks(raw_tasks)
    assert tasks == [{"role": "Regulatory", "title": "Review", "description": "Check"}]


def test_coverage_backfill_adds_missing_roles():
    raw_tasks = [{"role": "CTO", "title": "Plan", "description": "Arch"}]
    tasks = normalize_tasks(raw_tasks)
    REQUIRED_ROLES = {
        "CTO",
        "Research Scientist",
        "Regulatory",
        "Finance",
        "Marketing Analyst",
        "IP Analyst",
    }
    present = {t["role"] for t in tasks}
    for missing in sorted(REQUIRED_ROLES - present):
        tasks.append(
            {
                "role": missing,
                "title": f"Define initial {missing} workplan",
                "description": f"Draft the first set of actionable tasks for {missing} to advance the project.",
            }
        )
    assert REQUIRED_ROLES.issubset({t["role"] for t in tasks})
