"""Dry-run checks for Plan v1 planning artifacts.

Criteria covered:
1.1 concept brief template
1.2 role cards
1.3 task segmentation plan
1.4 redaction policy binding
"""

from pathlib import Path


def test_concept_brief_template_exists():
    """1.1 Concept brief template exists."""
    path = Path("docs/concept_brief.md")
    assert path.is_file(), "Concept brief template missing"


def test_role_cards_exist():
    """1.2 Role cards exist for Planner/PM and other agents."""
    roles_dir = Path("docs/roles")
    assert roles_dir.is_dir() and any(roles_dir.glob("*.md")), "Role cards missing"


def test_task_segmentation_plan_structure():
    """1.3 Task segmentation plan exists as structured data."""
    plan_dir = Path("planning")
    candidates = list(plan_dir.glob("*.yaml")) + list(plan_dir.glob("*.yml")) + list(plan_dir.glob("*.json"))
    assert candidates, "Task segmentation plan file missing"
    path = candidates[0]
    if path.suffix in {".yaml", ".yml"}:
        import yaml
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        import json
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    assert isinstance(data, dict) and data, "Task plan not structured as dict"
    first_role = next(iter(data.values()))
    assert "tasks" in first_role and isinstance(first_role["tasks"], list) and first_role["tasks"], (
        "Task plan lacks role->tasks list"
    )
    first_task = first_role["tasks"][0]
    assert "inputs" in first_task and "outputs" in first_task, "Task missing inputs/outputs"


def test_redaction_policy_bound_in_planning_prompts():
    """1.4 Redaction policy bound into planning prompts."""
    prompt_paths = list(Path("prompts").rglob("*.py")) + list(Path("core/agents").glob("*planner*.py"))
    found = False
    for path in prompt_paths:
        with path.open("r", encoding="utf-8") as f:
            text = f.read().lower()
        if "redact" in text or "redaction" in text:
            found = True
            break
    assert found, "Redaction policy missing from planning prompts"

