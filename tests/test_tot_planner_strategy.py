import importlib


def test_tot_strategy_adds_clarification_task_when_requirements_missing():
    from planning.strategies.tot import ToTPlannerStrategy

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


def test_tot_strategy_heuristic_when_no_evaluators(monkeypatch):
    monkeypatch.setenv("EVALUATORS_ENABLED", "true")
    from planning.strategies import tot as tot_module

    importlib.reload(tot_module)
    monkeypatch.setattr(tot_module.EvaluatorRegistry, "list", lambda: [])

    planner = tot_module.ToTPlannerStrategy()
    state = {"idea": "novel gadget", "scorecard": {"overall": 0.0, "metrics": {}}}

    tasks1 = planner.plan(state)
    tasks2 = planner.plan(state)

    assert tasks1 == tasks2

    # restore module state for other tests
    monkeypatch.setenv("EVALUATORS_ENABLED", "false")
    importlib.reload(tot_module)

