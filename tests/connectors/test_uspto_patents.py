import json
from pathlib import Path

from dr_rd.connectors import uspto_patents


def test_search_caching(tmp_path, monkeypatch):
    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1] / "fixtures" / "connectors" / "uspto_search.json"
        ).read_text()
    )
    calls = {"n": 0}

    def fake_http_json(url, params=None, headers=None, retries=3, timeout=10):
        calls["n"] += 1
        return fixture

    monkeypatch.setattr(uspto_patents, "http_json", fake_http_json)
    q = f"widget-{tmp_path}"
    res1 = uspto_patents.search_patents(q)
    res2 = uspto_patents.search_patents(q)
    assert calls["n"] == 1
    assert res1 == res2
    rec = res1["items"][0]
    assert rec["pub_number"] == "US1234567A"
    assert rec["assignees"] == ["Widgets Inc"]
