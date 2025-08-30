from utils import pricing


def test_table_has_defaults():
    tbl = pricing.table()
    assert tbl["openai:gpt-4o-mini"]["input_per_1k"] == 0.15
    assert pricing.get("anthropic:claude-3-5-sonnet") == {"input_per_1k": 3.0, "output_per_1k": 15.0}
