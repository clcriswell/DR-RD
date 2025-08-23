"""
Build SDD + ImplPlan from agent outputs without changing existing flow.
"""

from typing import Any, Dict

from core.spec.models import *


def _safe(x, default=""):
    return x if x else default


def assemble_from_agent_payloads(
    project_name: str, idea: str, answers: Dict[str, str]
) -> tuple[SDD, ImplPlan]:
    # Very light extraction: look for JSON blocks in agent answers; fall back to text.
    import json
    import re

    findings_by_role: Dict[str, Dict[str, Any]] = {}
    for role, text in answers.items():
        m = re.search(
            r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE
        )
        payload = {}
        if m:
            try:
                payload = json.loads(m.group(1))
            except Exception:
                payload = {}
        findings_by_role[role] = payload if isinstance(payload, dict) else {}
    # SDD
    reqs = [
        Requirement(id=f"R{i+1}", text=t)
        for i, t in enumerate(
            (findings_by_role.get("CTO", {}).get("requirements") or [])[:12]
        )
    ]
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
    sec = [
        SecurityReq(id=f"S{i+1}", control=t)
        for i, t in enumerate(
            (
                findings_by_role.get("CTO", {}).get("security")
                or findings_by_role.get("Compliance", {}).get("controls")
                or []
            )[:12]
        )
    ]
    risks_src = (
        (findings_by_role.get("IP Analyst", {}).get("risks") or [])
        + (findings_by_role.get("Regulatory", {}).get("risks") or [])
        + (findings_by_role.get("CTO", {}).get("risks") or [])
    )
    risks = [RiskItem(id=f"K{i+1}", text=str(r)) for i, r in enumerate(risks_src[:20])]
    sdd = SDD(
        title=f"{project_name} — System Design Doc",
        overview=_safe(
            findings_by_role.get("Research Scientist", {}).get("summary") or ""
        ),
        requirements=reqs,
        architecture=_safe(findings_by_role.get("CTO", {}).get("architecture") or ""),
        interfaces=interfaces,
        data_flows=dataflows,
        security=sec,
        risks=risks,
    )
    # ImplPlan
    w = [
        WorkItem(id=f"W{i+1}", title=str(t))
        for i, t in enumerate(
            (findings_by_role.get("CTO", {}).get("next_steps") or [])[:20]
        )
    ]
    ms = [
        Milestone(id=f"M{i+1}", name=str(m))
        for i, m in enumerate(
            (findings_by_role.get("Marketing Analyst", {}).get("milestones") or [])[:10]
        )
    ]
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
