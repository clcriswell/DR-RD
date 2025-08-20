import os
import glob


def test_concept_brief_template_exists():
    assert os.path.exists("docs/concept_brief.md"), "Concept brief template missing"


def test_role_cards_exist():
    assert glob.glob("docs/roles/*.md"), "Role cards missing"


def test_task_segmentation_plan_structure():
    candidates = glob.glob("planning/*.yaml") + glob.glob("planning/*.yml") + glob.glob("planning/*.json")
    assert candidates, "Task segmentation plan file missing"
    path = candidates[0]
    if path.endswith((".yaml", ".yml")):
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    assert isinstance(data, dict) and data, "Task plan not structured as dict"
    any_role = next(iter(data.values()))
    assert "tasks" in any_role, "Task plan lacks role->tasks mapping"


def test_redaction_policy_bound_in_planning_prompts():
    prompt_files = glob.glob("prompts/*.py") + glob.glob("prompts/**/*.py", recursive=True) + glob.glob("core/agents/*planner*.py")
    found = False
    for path in prompt_files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()
        if "redact" in text or "redaction" in text:
            found = True
            break
    assert found, "Redaction policy missing from planning prompts"

