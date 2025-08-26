from core.dashboard import aggregate
from config import feature_flags as ff

STORE = {
    "p1": {
        "runs": [
            {"ts": 1, "tasks": 2, "tool_calls": 3, "retrieval_calls": 1, "cost_usd": 0.5, "wall_time_s": 10, "evaluator_score": 0.8}
        ]
    },
    "p2": {
        "runs": [
            {"ts": 2, "tasks": 1, "tool_calls": 1, "retrieval_calls": 0, "cost_usd": 0.2, "wall_time_s": 5}
        ]
    },
}


def test_metrics_and_compare():
    projects = aggregate.list_projects(STORE)
    assert len(projects) == 2
    m = aggregate.collect_project_metrics(STORE["p1"])
    assert m["tasks_count"] == 2
    comp = aggregate.compare_projects(["p1", "p2", "p3"], store=STORE)
    assert set(comp.keys()) == {"p1", "p2"}


def test_compare_cap():
    ids = [f"p{i}" for i in range(ff.DASHBOARD_MAX_COMPARE + 2)]
    comp = aggregate.compare_projects(ids, store=STORE)
    assert len(comp) <= ff.DASHBOARD_MAX_COMPARE
