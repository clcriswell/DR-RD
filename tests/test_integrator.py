from core.summarization.integrator import integrate
from core.summarization.schemas import RoleSummary


def test_integrator_detects_contradictions():
    rs1 = RoleSummary(role="A", bullets=["Use plastic casing"])
    rs2 = RoleSummary(role="B", bullets=["Do not use plastic casing"])
    result = integrate([rs1, rs2])
    assert result.plan_summary
    assert result.key_findings
    assert result.contradictions
