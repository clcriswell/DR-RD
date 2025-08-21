"""Dry-run checks for Plan v1 planning artifacts."""

from pathlib import Path


def test_concept_brief_template_exists():
    path = Path("docs/concept_brief.md")
    assert path.is_file(), "Concept brief template missing"


def test_role_cards_exist():
    roles_dir = Path("docs/roles")
    assert roles_dir.is_dir() and any(roles_dir.glob("*.md")), "Role cards missing"


def test_task_segmentation_plan_structure():
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
    any_role = next(iter(data.values()))
    assert "tasks" in any_role, "Task plan lacks role->tasks mapping"


def test_redaction_policy_bound_in_planning_prompts():
    prompt_paths = list(Path("prompts").rglob("*.py")) + list(Path("core/agents").glob("*planner*.py"))
    found = False
    for path in prompt_paths:
        with path.open("r", encoding="utf-8") as f:
            text = f.read().lower()
        if "redact" in text or "redaction" in text:
            found = True
            break
    assert found, "Redaction policy missing from planning prompts"

