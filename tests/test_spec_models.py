from core.spec.models import (
    Requirement,
    Interface,
    DataFlow,
    SecurityReq,
    RiskItem,
    Milestone,
    WorkItem,
    BOMItem,
    BudgetPhase,
    SDD,
    ImplPlan,
)


def test_model_defaults():
    r = Requirement(id="R1", text="Req")
    assert r.priority == "M"
    i = Interface(name="IF1", producer="A", consumer="B", contract="C")
    d = DataFlow(source="A", sink="B", data="D")
    assert d.frequency == ""
    s = SecurityReq(id="S1", control="ctl")
    assert s.rationale == ""
    k = RiskItem(id="K1", text="Risk")
    assert k.severity == "H" and k.mitigation == ""
    m = Milestone(id="M1", name="Mil")
    assert m.due == "" and m.deliverables == []
    w = WorkItem(id="W1", title="Work")
    assert w.owner == "TBD" and w.deps == []
    b = BOMItem(part_no="P1", desc="Part")
    assert b.qty == 1 and b.unit_cost == 0.0 and b.vendor == "TBD"
    bp = BudgetPhase(phase="Phase")
    assert bp.cost_usd == 0.0
    sdd = SDD(title="T", overview="O", architecture="Arch")
    assert sdd.requirements == []
    impl = ImplPlan()
    assert impl.work == [] and impl.milestones == [] and impl.rollback == ""
