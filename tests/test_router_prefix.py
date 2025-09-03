import core.router as router

def _choose(task_id, title="Task", summary="Do work"):
    t = {"id": task_id, "title": title, "summary": summary}
    role, _cls, _model = router.choose_agent_for_task(None, title, summary, task=t)
    return role


def test_dev_prefix_routes_to_cto():
    assert _choose("DEV_1") == "CTO"


def test_qa_prefix_routes_to_qa():
    assert _choose("QA_1") == "QA"


def test_mkt_prefix_routes_to_marketing():
    assert _choose("MKT_1") == "Marketing Analyst"


def test_unknown_prefix_falls_back():
    assert _choose("XYZ_1") == "Dynamic Specialist"
