import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DIMENSIONS = [
    "Feasibility",
    "Novelty",
    "Compliance",
    "Cost",
    "IP",
    "Market",
    "Architecture",
    "Materials",
]


def _to_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (bool, int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return " ".join(_to_text(x) for x in v)
    if isinstance(v, dict):
        preferred = [
            "summary",
            "text",
            "content",
            "title",
            "description",
            "findings",
            "claim",
            "body",
        ]
        for key in preferred:
            if key in v and v[key] is not None:
                val = _to_text(v[key])
                if val:
                    return val
        parts = [
            _to_text(value)
            for value in v.values()
            if value is not None and _to_text(value)
        ]
        if parts:
            return " ".join(parts)
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return str(v)


def build_coverage(project_id: str, role_to_findings: Dict[str, dict]) -> List[Dict]:
    rows = []
    for role, payload in role_to_findings.items():
        dims = {d: False for d in DIMENSIONS}
        findings_raw = payload.get("findings")
        task_raw = payload.get("task")
        txt = _to_text(findings_raw) + " " + _to_text(task_raw)
        if any(isinstance(x, (list, tuple, dict)) for x in [findings_raw, task_raw]):
            logger.info("coverage: coerced structured fields for role=%s", role)
        t = txt.lower()
        dims["Feasibility"] = any(k in t for k in ["feasible", "feasibility", "risk", "resource"])
        dims["Novelty"] = any(k in t for k in ["novel", "original", "prior art", "new"])
        dims["Compliance"] = any(k in t for k in ["regulatory", "compliance", "fda", "iso", "safety"])
        dims["Cost"] = any(k in t for k in ["cost", "budget", "capex", "opex", "bom"])
        dims["IP"] = any(k in t for k in ["patent", "prior art", "claims", "freedom to operate", "ip"])
        dims["Market"] = any(k in t for k in ["market", "customer", "adoption", "pricing", "competitor"])
        dims["Architecture"] = any(k in t for k in ["architecture", "interface", "security", "scalability", "system"])
        dims["Materials"] = any(k in t for k in ["material", "alloy", "polymer", "composite", "fatigue", "tensile"])
        row = {"project_id": project_id, "role": role}
        row.update(dims)
        rows.append(row)
    return rows
