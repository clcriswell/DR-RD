import requests

from scripts.dead_link_check import check_links


class FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


def test_dead_link_check(tmp_path, monkeypatch):
    doc = tmp_path / "doc.md"
    doc.write_text("[bad](missing.md)\n[ext](https://example.com/404)\n")

    monkeypatch.setattr(requests, "head", lambda *a, **k: FakeResp(404))

    result = check_links([doc])
    assert result["internal_errors"]
    assert result["external_warnings"]
