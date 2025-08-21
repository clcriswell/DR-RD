from typing import List, Dict

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


def build_coverage(project_id: str, role_to_findings: Dict[str, dict]) -> List[Dict]:
    rows = []
    for role, payload in role_to_findings.items():
        dims = {d: False for d in DIMENSIONS}
        txt = (payload.get("findings") or "") + " " + (payload.get("task") or "")
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
