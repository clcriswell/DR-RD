import json

from core.router import route_task
from prompts.prompts import PLANNER_SYSTEM_PROMPT


def test_unknown_role_falls_back():
    task = {"id": "T1", "role": "Unknown", "title": "x", "description": "y"}
    role, cls, model, out = route_task(task)
    assert role == "Dynamic Specialist"


def test_planner_prompt_has_no_redactions():
    assert "redacted" not in PLANNER_SYSTEM_PROMPT.lower()
