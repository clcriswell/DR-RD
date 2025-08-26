import time

import config.feature_flags as ff


def test_graph_parallelism(monkeypatch):
    ff.PARALLEL_EXEC_ENABLED = True
    ff.EVALUATORS_ENABLED = False

    def fake_plan(idea, constraint_text, risk, ui_model=None):
        return [
            {"id": "t1", "title": "a", "description": "b"},
            {"id": "t2", "title": "a", "description": "b"},
        ]

    def fake_route(task, ui_model=None):
        return "Role", None, None, {"id": task["id"], "role": "Role", "title": "a", "description": "b"}

    def fake_dispatch(task, ui_model=None):
        time.sleep(0.2)
        return {"content": "done"}

    def fake_compose(idea, answers):
        return "done"

    monkeypatch.setattr("core.orchestrator.generate_plan", fake_plan)
    monkeypatch.setattr("core.router.route_task", fake_route)
    monkeypatch.setattr("core.router.dispatch", fake_dispatch)
    monkeypatch.setattr("core.orchestrator.compose_final_proposal", fake_compose)

    from core.graph.graph import run_langgraph

    start = time.time()
    run_langgraph("idea", max_concurrency=1)
    sequential = time.time() - start

    start = time.time()
    run_langgraph("idea", max_concurrency=2)
    parallel = time.time() - start

    assert parallel < sequential
