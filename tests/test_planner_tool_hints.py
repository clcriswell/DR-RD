from core.schemas import Plan, Task
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks


def test_plan_tool_request_survives_normalization():
    plan = Plan(
        tasks=[
            Task(
                id="T1",
                role="Research Scientist",
                title="Run sim",
                summary="",
                description="Simulate",
                tool_request={"tool": "simulate", "params": {"inputs": {"a": 1.0}}},
            )
        ]
    )
    raw = [t.model_dump() for t in plan.tasks]
    norm = normalize_tasks(normalize_plan_to_tasks(raw))
    assert norm[0]["tool_request"]["tool"] == "simulate"
