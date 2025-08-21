from core.poc.testplan import Metric, TestCase, TestPlan
from core.orchestrator import run_poc


def test_poc_wiring():
    tc = TestCase(
        id="T1",
        title="Thermal",
        inputs={"power_w": 10, "ambient_c": 25, "_sim": "thermal_mock"},
        metrics=[Metric(name="delta_c", target=1.0, operator="<=")],
    )
    plan = TestPlan(project_id="proj", hypothesis="h", tests=[tc])
    report = run_poc("proj", plan)
    assert report.results and report.results[0].metrics_observed["delta_c"] == 1.0
