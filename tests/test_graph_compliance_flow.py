from core.graph.state import GraphState, GraphTask
from core.graph.nodes import compliance_node
from config import feature_flags as ff


def test_compliance_node(monkeypatch):
    ff.COMPLIANCE_ENABLED = True
    task = GraphTask(
        id="T1",
        title="check",
        description="",
        role="Regulatory",
        compliance_request={"profile_ids": ["us_federal"], "min_coverage": 0.1},
    )
    state = GraphState(
        idea="", constraints=[], risk_posture="", tasks=[task], cursor=0,
        answers={"T1": {"content": "We follow FDA guidelines."}}, trace=[], tool_trace=[], retrieved={}
    )
    state.answers["T1"]["retrieval_sources"] = [
        {"id": "s1", "url": "https://federalregister.gov/doc/1"}
    ]
    compliance_node(state)
    report = state.answers["T1"].get("compliance")
    assert report and "coverage" in report
