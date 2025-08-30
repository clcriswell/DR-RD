from core.role_normalizer import (
    SYNONYMS,
    group_by_role,
    normalize_role,
    normalize_tasks,
)

ALLOWED = set(SYNONYMS.keys())


def test_exact_match():
    assert normalize_role("CTO", ALLOWED) == "CTO"


def test_synonym_mapping():
    assert normalize_role("Mechanical Engineer", ALLOWED) == "Mechanical Systems Lead"


def test_fuzzy_fallback():
    assert normalize_role("Reserch Scientst", ALLOWED) == "Research Scientist"


def test_tail_collapse_by_frequency():
    tasks = [
        {"role": "CTO", "title": "t1", "description": "d"},
        {"role": "Finance", "title": "t2", "description": "d"},
        {"role": "Finance", "title": "t3", "description": "d"},
    ]
    normalized = normalize_tasks(tasks, allowed_roles=ALLOWED, max_roles=1)
    roles = [t["normalized_role"] for t in normalized]
    assert roles.count("Finance") == 2
    assert roles.count("Synthesizer") == 1
    assert "CTO" not in roles


def test_paperclip_plan_grouping():
    tasks = [
        {
            "role": "Mechanical Engineer",
            "title": "Design extruder",
            "description": "Build the machine",
        },
        {
            "role": "Regulatory/Compliance Specialist",
            "title": "Check safety",
            "description": "Ensure compliance",
        },
        {
            "role": "Product Manager",
            "title": "Analyze market",
            "description": "Assess demand",
        },
        {
            "role": "Product Manager",
            "title": "Plan launch",
            "description": "Coordinate release",
        },
    ]
    normalized = normalize_tasks(tasks, allowed_roles=ALLOWED)
    grouped = group_by_role(normalized, key="normalized_role")
    assert set(grouped) == {"Mechanical Systems Lead", "Regulatory", "Planner"}
    assert len(grouped["Planner"]) == 2


def test_handles_string_tasks():
    tasks = ["do something"]
    normalized = normalize_tasks(tasks, allowed_roles=ALLOWED)
    assert normalized[0]["normalized_role"] == "Synthesizer"
