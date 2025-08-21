from core.observability import build_coverage


def test_build_coverage():
    role_to_findings = {
        "Researcher": {
            "findings": "Feasibility looks good and cost is low",
            "task": "Study market and compliance",
        },
        "Engineer": {"findings": "Uses novel materials", "task": ""},
    }
    rows = build_coverage("p1", role_to_findings)
    assert len(rows) == 2
    r1 = {r["role"]: r for r in rows}["Researcher"]
    assert r1["Feasibility"] and r1["Cost"] and r1["Compliance"]
    r2 = {r["role"]: r for r in rows}["Engineer"]
    assert r2["Materials"] and r2["Novelty"]
