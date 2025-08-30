from utils.prompts import loader


def test_load_and_hash():
    prompts = loader.load_all()
    assert "planner" in prompts
    h1 = loader.hash_prompt(prompts["planner"])
    import copy, yaml
    obj = copy.deepcopy(prompts["planner"])
    text = yaml.safe_dump(obj, sort_keys=True)
    obj2 = yaml.safe_load(text)
    h2 = loader.hash_prompt(obj2)
    assert h1 == h2


def test_validate_schema_errors():
    bad = {"id": "x", "template": "hi {a}"}
    problems = loader.validate(bad)
    assert any("missing version" in p for p in problems)
    assert any("placeholder a not declared" in p for p in problems)
