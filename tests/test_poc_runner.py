from simulation.registry import register
from core.poc.testplan import Metric, TestCase, TestPlan
from core.orchestrator import run_poc


@register("dummy_sim")
def _dummy(inputs):
    return {"val": inputs.get("x", 0)}, {"cost_estimate_usd": 0.0, "seconds": 0.0, "backend": "dummy"}


def test_poc_runner():
    tc = TestCase(
        id="t1",
        title="demo",
        inputs={"x": 5, "_sim": "dummy_sim"},
        metrics=[Metric(name="val", target=4, operator=">=")],
    )
    plan = TestPlan(project_id="p1", hypothesis="h", tests=[tc])
    report = run_poc("p1", plan)
    assert report.results[0].passed is True
