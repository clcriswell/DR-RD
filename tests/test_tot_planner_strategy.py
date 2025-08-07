from dr_rd.planning.strategies.tot import ToTPlannerStrategy


def test_tot_strategy_adds_clarification_task_when_requirements_missing():
    state = {"idea": "novel gadget"}
    baseline = [
        {
            "role": "Systems Integration & Validation Engineer",
            "task": "Prototype critical subsystems",
        }
    ]

    planner = ToTPlannerStrategy()
    tasks = planner.plan(state)

    assert isinstance(tasks, list) and tasks
    baseline_desc = {t["task"] for t in baseline}
    extra = [t for t in tasks if t["task"] not in baseline_desc]
    # ensure at least one additional task beyond the baseline
    assert extra
    # specifically ensure clarification is suggested for underspecified projects
    assert any("clarify" in t["task"].lower() for t in tasks)

