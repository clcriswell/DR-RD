import csv
import json
from pathlib import Path


def test_tasks_jsonl_parse():
    for path in Path("samples/tasks").glob("*.jsonl"):
        for line in path.read_text().splitlines():
            json.loads(line)


def test_fixtures_json():
    for path in Path("samples/connectors/fixtures").glob("*.json"):
        data = json.loads(path.read_text())
        assert isinstance(data, dict)


def test_materials_csv():
    with open("samples/materials/materials_properties.csv") as fh:
        reader = csv.DictReader(fh)
        assert set(reader.fieldnames) == {"name", "property", "value", "units", "source"}
        rows = list(reader)
        assert rows
