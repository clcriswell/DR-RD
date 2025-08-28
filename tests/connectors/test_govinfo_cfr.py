import json
from pathlib import Path

from dr_rd.connectors import govinfo_cfr


def test_lookup(tmp_path, monkeypatch):
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1] / "fixtures" / "connectors" / "cfr_lookup.json"
        ).read_text()
    )
    monkeypatch.setattr(govinfo_cfr, "http_json", lambda *a, **k: fixture)
    res = govinfo_cfr.lookup_cfr("40", "60", "1")
    assert res["text"] == "CFR text here"
    assert "url" in res
