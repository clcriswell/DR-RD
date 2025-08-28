import json
from pathlib import Path

from dr_rd.connectors import regulations_gov


def test_search(tmp_path, monkeypatch):
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "connectors"
            / "regulations_search.json"
        ).read_text()
    )
    monkeypatch.setattr(regulations_gov, "http_json", lambda *a, **k: fixture)
    res = regulations_gov.search_documents("epa")
    assert res["items"][0]["agency"] == "EPA"
    assert res["items"][0]["cfr_refs"] == ["40 CFR 60"]
