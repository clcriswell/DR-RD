from utils.eval import datasets
import json


def test_load_and_normalize_jsonl(tmp_path):
    p = tmp_path / "d.jsonl"
    with p.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "a", "idea": "hi", "expected_keywords": "foo,bar"}) + "\n")
    items = datasets.load_jsonl(str(p))
    norm = datasets.normalize(items)
    assert norm[0]["id"] == "a"
    assert norm[0]["mode"] == "standard"
    assert norm[0]["expected_keywords"] == ["foo", "bar"]


def test_load_and_normalize_csv(tmp_path):
    p = tmp_path / "d.csv"
    with p.open("w", encoding="utf-8") as f:
        f.write("id,idea,expected_keywords\n")
        f.write('a,hi,"foo,bar"\n')
    items = datasets.load_csv(str(p))
    norm = datasets.normalize(items)
    assert norm[0]["id"] == "a"
    assert norm[0]["expected_keywords"] == ["foo", "bar"]


def test_duplicate_ids_rejected():
    items = [{"id": "a"}, {"id": "a"}]
    try:
        datasets.normalize(items)
    except ValueError:
        return
    assert False, "duplicate id not detected"
