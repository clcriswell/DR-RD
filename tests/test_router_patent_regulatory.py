
from core import tool_router


def test_router_patent_provenance(monkeypatch):
    def fake_search(params, caps):
        return [{"id": "p1"}]

    monkeypatch.setattr(
        tool_router.patent_adapters, "search_patents", fake_search
    )
    tool_router._PROVENANCE.clear()
    res = tool_router.call_tool("agent", "patent_search", {"q": "x"})
    assert res[0]["id"] == "p1"
    assert tool_router.get_provenance()


def test_router_regulatory_provenance(monkeypatch):
    def fake_search(params, caps):
        return [{"id": "r1"}]

    monkeypatch.setattr(
        tool_router.reg_adapters, "search_regulations", fake_search
    )
    tool_router._PROVENANCE.clear()
    res = tool_router.call_tool("agent", "regulatory_search", {"q": "x"})
    assert res[0]["id"] == "r1"
    assert tool_router.get_provenance()
