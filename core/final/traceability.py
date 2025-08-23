"""
Build rows linking intake → plan tasks → routed agent → artifact paths → final sections.
"""

from typing import Dict, List


def build_rows(
    project_id: str,
    intake: Dict,
    tasks: List[Dict],
    routing_report: List[Dict],
    answers: Dict[str, str],
    artifacts: Dict[str, str],
) -> List[Dict[str, str]]:
    rows = []
    for t in tasks or []:
        planned_role = t.get("role", "")
        title = t.get("title", "")
        routed = next((r for r in routing_report if r.get("title") == title), {})
        final_role = routed.get("final_role", planned_role)
        rows.append(
            {
                "project_id": project_id,
                "idea": (intake or {}).get("idea", "")[:120],
                "constraints": "; ".join(
                    (intake or {}).get("constraints", [])
                    if isinstance((intake or {}).get("constraints"), list)
                    else [str((intake or {}).get("constraints", ""))]
                ).strip(),
                "task_title": title,
                "planned_role": planned_role,
                "final_role": final_role,
                "agent_answer_len": str(len((answers or {}).get(final_role, ""))),
                "artifact_evidence": artifacts.get("evidence", ""),
                "artifact_coverage": artifacts.get("coverage", ""),
                "artifact_decisions": artifacts.get("decision_log", ""),
                "final_section_hint": "Research Findings",
            }
        )
    return rows
