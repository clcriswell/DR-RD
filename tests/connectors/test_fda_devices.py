import json
from pathlib import Path

from dr_rd.connectors import fda_devices


def test_device_search(tmp_path, monkeypatch):
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1] / "fixtures" / "connectors" / "fda_search.json"
        ).read_text()
    )
    monkeypatch.setattr(fda_devices, "http_json", lambda *a, **k: fixture)
    res = fda_devices.search_devices("widget")
    assert res["items"][0]["k_number"] == "K123456"
