import json

from dr_rd.prompting.prompt_registry import registry


def test_marketing_template_has_fields():
    tpl = registry.get("Marketing Analyst")
    assert "summary" in tpl.user_template and "findings" in tpl.user_template
    assert "next_steps" in tpl.user_template and "sources" in tpl.user_template


def test_finance_template_has_fields():
    tpl = registry.get("Finance")
    for key in [
        "unit_economics",
        "npv",
        "simulations",
        "assumptions",
        "risks",
        "next_steps",
        "sources",
    ]:
        assert key in tpl.user_template


def test_cto_template_has_fields():
    tpl = registry.get("CTO")
    for key in ["summary", "findings", "next_steps", "sources"]:
        assert key in tpl.user_template


def test_dynamic_and_qa_templates():
    dyn = registry.get("Dynamic Specialist")
    qa = registry.get("QA")
    assert "findings" in dyn.system and dyn.io_schema_ref.endswith("generic_v2.json")
    assert qa.io_schema_ref.endswith("qa_v2.json")
    assert "JSON summary" in qa.user_template


def test_qa_schema_uses_arrays():
    with open("dr_rd/schemas/qa_v2.json", encoding="utf-8") as fh:
        schema = json.load(fh)
    assert schema["properties"]["risks"]["type"] == "array"
    assert schema["properties"]["next_steps"]["type"] == "array"
