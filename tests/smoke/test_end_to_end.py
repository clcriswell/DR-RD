import json
from pathlib import Path


def test_end_to_end_offline():
    """Offline smoke test reading pre-generated JSON output."""
    fixture = Path("tests/fixtures/connectors/uspto_search.json")
    data = json.loads(fixture.read_text())
    assert isinstance(data, dict)
    sources = data.get("results") or data.get("sources")
    assert sources, "expected sources from fixture"
