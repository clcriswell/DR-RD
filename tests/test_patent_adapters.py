import pytest
from dr_rd.integrations.patents import adapters


def test_patent_normalization_and_caps(monkeypatch):
    sample = {
        "patents": [
            {
                "patent_number": "123",
                "title": "Widget",
                "abstract": "A widget",
                "assignees": [{"assignee_organization": "ACME"}],
                "inventors": [
                    {"inventor_first_name": "Ann", "inventor_last_name": "Smith"}
                ],
                "cpc_subgroups": [{"cpc_subgroup_id": "G06F"}],
                "patent_date": "2020-01-01",
            }
        ]
    }

    def fake_http(url, params, timeout):
        return sample

    monkeypatch.setattr(adapters, "_http_get_json", fake_http)
    caps = {"backends": ["patentsview"], "max_results": 1, "timeouts_s": 5}
    res = adapters.search_patents({"q": "widget"}, caps)
    assert len(res) == 1
    assert res[0]["id"] == "123"
    assert res[0]["cpc"] == ["G06F"]
