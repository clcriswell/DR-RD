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
