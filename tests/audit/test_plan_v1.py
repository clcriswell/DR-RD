
"""Dry-run checks for Plan v1 planning artifacts."""

import os
import glob
import yaml


def test_concept_brief_template_exists():
    assert os.path.exists("docs/concept_brief.md"), "Concept brief template missing"


def test_role_cards_exist():
    assert glob.glob("docs/roles/*.md"), "Role cards missing"


def test_task_segmentation_plan_structure():
    path = "planning/task_plan.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for key in ["roles", "tasks", "inputs", "outputs", "redaction_policy"]:
        assert key in data, f"Missing key {key} in task plan"


def test_redaction_policy_bound_in_planning_prompts():
    prompt_files = glob.glob("prompts/*.md") + glob.glob("prompts/**/*.md", recursive=True)
    found = False
    for path in prompt_files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()
        if "redact" in text or "redaction" in text:
            found = True
            break
    assert found, "Redaction policy missing from planning prompts"

