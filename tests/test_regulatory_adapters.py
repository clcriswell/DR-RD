from dr_rd.integrations.regulatory import adapters


def test_regulatory_normalization(monkeypatch):
    fr_sample = {
        "results": [
            {
                "document_number": "1",
                "title": "Rule",
                "citation": "10 CFR 1",
                "publication_date": "2021-01-01",
                "html_url": "https://federalregister.gov/doc/1",
                "snippet": "snippet",
            }
        ]
    }

    def fake_http(url, params, timeout):
        return fr_sample

    monkeypatch.setattr(adapters, "_http_get_json", fake_http)
    caps = {"backends": ["federal_register"], "max_results": 10, "timeouts_s": 5}
    res = adapters.search_regulations({"q": "energy"}, caps)
    assert res and res[0]["jurisdiction"] == "US"
