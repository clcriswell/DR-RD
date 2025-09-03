from types import SimpleNamespace

import core.router as router


def test_routing_prefix_and_fallback(monkeypatch):
    monkeypatch.setattr(router, "st", SimpleNamespace(session_state={}))
    cases = [
        ("DEV_1", "CTO"),
        ("ENG_2", "CTO"),
        ("QA_3", "QA"),
        ("MKT_4", "Marketing Analyst"),
        ("IP_5", "IP Analyst"),
        ("REG_6", "Regulatory"),
        ("MAT_7", "Materials Engineer"),
        ("SIM_8", "Simulation"),
        ("XYZ_9", "Dynamic Specialist"),
    ]
    roles = []
    for tid, expected in cases:
        task = {"id": tid, "title": "task", "summary": "s"}
        role, _cls, _model, _routed = router.route_task(task)
        roles.append(role)
    assert roles == [exp for _tid, exp in cases]
    report = router.st.session_state["routing_report"]
    assert len(report) == len(cases)
    assert report[-1]["routed_role"] == "Dynamic Specialist"
