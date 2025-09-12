from __future__ import annotations

import json
from jsonschema import validate

from dr_rd.reporting import compose
from dr_rd.reporting.exporters import to_markdown, to_html


SCHEMA = json.load(open("dr_rd/reporting/schemas/report_v1.json"))


def test_compose_and_export(tmp_path):
    spec = {"report_id": "r1", "title": "T"}
    artifacts = {
        "agents": [
            {"role": "A", "title": "A", "body": "alpha {{s1}}", "sources": [{"id": "s1", "kind": "web", "url": "http://a", "title": "A"}]},
            {"role": "B", "title": "B", "body": "beta", "sources": []},
        ],
        "synth": {"executive_summary": "sum"},
    }
    report = compose(spec, artifacts)
    validate(report, SCHEMA)
    md = to_markdown(report)
    html = to_html(report)
    assert "# T" in md
    assert "<html" in html


def test_compose_includes_planner_fields():
    spec = {
        "report_id": "r1",
        "title": "T",
        "planner": {"constraints": ["C1"], "assumptions": ["A1"]},
    }
    artifacts = {"agents": [], "synth": {"executive_summary": ""}}
    report = compose(spec, artifacts)
    planner_meta = report["metadata"]["planner"]
    assert planner_meta["constraints"] == ["C1"]
    assert planner_meta["assumptions"] == ["A1"]


def test_compose_maps_risk_register_to_risks():
    risk_reg = [
        {"class": "policy", "likelihood": "low", "mitigation": "sanitize"}
    ]
    spec = {"report_id": "r1", "title": "T", "planner": {"risk_register": risk_reg}}
    artifacts = {"agents": [], "synth": {"executive_summary": ""}}
    report = compose(spec, artifacts)
    planner_meta = report["metadata"]["planner"]
    assert planner_meta["risk_register"] == risk_reg
    assert planner_meta["risks"] == ["policy"]


def test_markdown_includes_planner_fields():
    risk_reg = [
        {"class": "policy", "likelihood": "low", "mitigation": "sanitize"}
    ]
    spec = {
        "report_id": "r1",
        "title": "T",
        "planner": {
            "constraints": ["C1"],
            "assumptions": ["A1"],
            "risk_register": risk_reg,
        },
    }
    report = compose(spec, {"agents": [], "synth": {"executive_summary": ""}})
    md = to_markdown(report)
    assert "## Constraints / Assumptions" in md
    assert "- C1" in md and "- A1" in md
    assert "## Risks" in md
    assert "- policy" in md


def test_compose_groups_sections_by_group():
    spec = {"report_id": "r1", "title": "T"}
    artifacts = {
        "agents": [
            {"role": "A", "title": "A1", "body": "alpha", "group": "Phase 1"},
            {"role": "B", "title": "B1", "body": "beta", "group": "Phase 1"},
            {"role": "C", "title": "C1", "body": "gamma", "group": "Phase 2"},
        ],
        "synth": {"executive_summary": ""},
    }
    report = compose(spec, artifacts)
    assert [s.get("group") for s in report["sections"]] == [
        "Phase 1",
        "Phase 1",
        "Phase 2",
    ]
    md = to_markdown(report)
    assert "## Phase 1" in md and "## Phase 2" in md
    assert md.index("## Phase 1") < md.index("### A1") < md.index("### B1")
    assert md.index("## Phase 2") < md.index("### C1")
