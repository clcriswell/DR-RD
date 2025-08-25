from __future__ import annotations

from typing import List

from .schemas import IntegratedSummary, RoleSummary
from . import cross_reference_enabled


_NEG_WORDS = ["not", "avoid", "against", "do"]


def _is_contradiction(a: str, b: str) -> bool:
    base_a = a
    base_b = b
    for w in _NEG_WORDS:
        base_a = base_a.replace(w, "")
        base_b = base_b.replace(w, "")
    base_a = base_a.strip()
    base_b = base_b.strip()
    if not base_a or not base_b:
        return False
    if base_a == base_b and any(w in a or w in b for w in _NEG_WORDS):
        return True
    return False


def integrate(role_summaries: List[RoleSummary]) -> IntegratedSummary:
    """Integrate multiple ``RoleSummary`` objects into a holistic view."""

    key_findings: List[str] = []
    for rs in role_summaries:
        key_findings.extend([f"{rs.role}: {b}" for b in rs.bullets])

    plan_summary = "; ".join(
        f"{rs.role}: {rs.bullets[0]}" for rs in role_summaries if rs.bullets
    )

    contradictions: List[str] = []
    if cross_reference_enabled():
        for i, rs_a in enumerate(role_summaries):
            for rs_b in role_summaries[i + 1 :]:
                for a in rs_a.bullets:
                    for b in rs_b.bullets:
                        if _is_contradiction(a.lower(), b.lower()):
                            contradictions.append(
                                f"{rs_a.role} vs {rs_b.role}: {a} / {b}"
                            )
    return IntegratedSummary(
        plan_summary=plan_summary.strip(),
        key_findings=key_findings,
        contradictions=contradictions,
    )
