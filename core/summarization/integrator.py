from __future__ import annotations

from typing import Dict, List

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


def render_references(text: str, sources: List[Dict[str, str]]) -> str:
    """Append a References section for ``sources`` to ``text``.

    Sources are deduplicated by their ``source_id`` and rendered in numeric order.
    """

    if not sources:
        return text
    unique: Dict[str, Dict[str, str]] = {}
    for src in sources:
        sid = src.get("source_id") or f"S{len(unique) + 1}"
        if sid not in unique:
            unique[sid] = src
    ordered = [unique[k] for k in sorted(unique, key=lambda x: int(str(x).lstrip("S")))]
    lines = ["\n\n## References"]
    for src in ordered:
        sid = src.get("source_id")
        title = src.get("title") or src.get("url", "")
        url = src.get("url", "")
        lines.append(f"[{sid}] {title} ({url})".strip())
    return text + "\n" + "\n".join(lines)


__all__ = ["integrate", "render_references"]
