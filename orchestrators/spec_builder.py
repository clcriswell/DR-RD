"""
Build SDD + ImplPlan from agent outputs without changing existing flow.
"""
from typing import Dict, Any
from core.spec.models import *


def _safe(x, default: str = "(This section was not completed in this research pass.)"):
    if not x or x == "Not determined":
        return default
    return x


def assemble_from_agent_payloads(project_name: str, idea: str, answers: Dict[str, str]) -> tuple[SDD, ImplPlan]:
    # Very light extraction: look for JSON blocks in agent answers; fall back to text.
    import re, json

    findings_by_role: Dict[str, Dict[str, Any]] = {}
    for role, text in answers.items():
        m = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
        payload = {}
        if m:
            try:
                payload = json.loads(m.group(1))
            except Exception:
                payload = {}
        findings_by_role[role] = payload if isinstance(payload, dict) else {}
    # SDD
    reqs = []
    for i, t in enumerate((findings_by_role.get("CTO", {}).get("requirements") or [])[:12]):
        if t and t != "Not determined":
            reqs.append(Requirement(id=f"R{i+1}", text=t))
    interfaces = [
        Interface(**it)
        for it in (findings_by_role.get("CTO", {}).get("interfaces") or [])
        if isinstance(it, dict)
    ]
    dataflows = [
        DataFlow(**it)
        for it in (findings_by_role.get("CTO", {}).get("data_flows") or [])
        if isinstance(it, dict)
    ]
    sec = []
    for i, t in enumerate(
        (
            findings_by_role.get("CTO", {}).get("security")
            or findings_by_role.get("Compliance", {}).get("controls")
            or []
        )[:12]
    ):
        if t and t != "Not determined":
            sec.append(SecurityReq(id=f"S{i+1}", control=t))
    risks_src = (
        findings_by_role.get("IP Analyst", {}).get("risks") or []
    ) + (
        findings_by_role.get("Regulatory", {}).get("risks") or []
    ) + (
        findings_by_role.get("CTO", {}).get("risks") or []
    )
    risks = []
    for i, r in enumerate(risks_src[:20]):
        if r and r != "Not determined":
            risks.append(RiskItem(id=f"K{i+1}", text=str(r)))
    sdd = SDD(
        title=f"{project_name} — System Design Doc",
        overview=_safe(findings_by_role.get("Research Scientist", {}).get("summary") or ""),
        requirements=reqs,
        architecture=_safe(findings_by_role.get("CTO", {}).get("architecture") or ""),
        interfaces=interfaces,
        data_flows=dataflows,
        security=sec,
        risks=risks,
    )
    # ImplPlan
    w = []
    for i, t in enumerate((findings_by_role.get("CTO", {}).get("next_steps") or [])[:20]):
        if t and t != "Not determined":
            w.append(WorkItem(id=f"W{i+1}", title=str(t)))
    ms = []
    for i, m in enumerate((findings_by_role.get("Marketing Analyst", {}).get("milestones") or [])[:10]):
        if m and m != "Not determined":
            ms.append(Milestone(id=f"M{i+1}", name=str(m)))
    bom = [
        BOMItem(**it)
        for it in (findings_by_role.get("Finance", {}).get("bom") or [])
        if isinstance(it, dict)
    ]
    budget = [
        BudgetPhase(**it)
        for it in (findings_by_role.get("Finance", {}).get("budget") or [])
        if isinstance(it, dict)
    ]
    impl = ImplPlan(
        work=w,
        milestones=ms,
        rollback=_safe(findings_by_role.get("CTO", {}).get("rollback") or ""),
        bom=bom,
        budget=budget,
    )
    return sdd, impl
