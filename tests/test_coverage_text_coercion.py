from core.observability.coverage import _to_text, build_coverage


def test_dict_preferred_keys():
    findings = {"summary": "Feasible design"}
    task = {"title": "Study cost"}
    assert _to_text(findings) == "Feasible design"
    assert _to_text(task) == "Study cost"
    rows = build_coverage("p", {"r": {"findings": findings, "task": task}})
    assert rows[0]["Feasibility"] and rows[0]["Cost"]


def test_list_and_dict_items():
    findings = ["novel approach", "market analysis"]
    task = [{"text": "reduce cost"}]
    txt_findings = _to_text(findings)
    txt_task = _to_text(task)
    assert "novel approach" in txt_findings and "market analysis" in txt_findings
    assert "reduce cost" in txt_task
    rows = build_coverage("p", {"r": {"findings": findings, "task": task}})
    assert rows[0]["Novelty"] and rows[0]["Market"] and rows[0]["Cost"]


def test_dict_without_preferred_keys():
    findings = {"foo": {"bar": "baz"}}
    txt = _to_text(findings)
    assert txt
    build_coverage("p", {"r": {"findings": findings, "task": ""}})


def test_none_and_empty_strings():
    rows = build_coverage("p", {"r": {"findings": None, "task": ""}})
    assert not any(rows[0][d] for d in rows[0] if d not in {"project_id", "role"})
