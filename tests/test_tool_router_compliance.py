import jsonschema
import pytest

from core import tool_router
from dr_rd.connectors import uspto_patents


def _allow():
    tool_router.allow_tools("tester", ["patent_search"])
    tool_router._REGISTRY["patent_search"].calls = 0


def test_schema_validation():
    _allow()
    with pytest.raises(jsonschema.ValidationError):
        tool_router.call_tool("tester", "patent_search", {})


def test_caps(monkeypatch, tmp_path):
    _allow()
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    tool_router.TOOL_CONFIG["PATENT_SEARCH"]["max_calls"] = 1
    monkeypatch.setattr(uspto_patents, "http_json", lambda *a, **k: {"results": []})
    tool_router.call_tool("tester", "patent_search", {"query": "x1"})
    out = tool_router.call_tool("tester", "patent_search", {"query": "x2"})
    assert out["ok"] is False


def test_provenance(monkeypatch, tmp_path):
    _allow()
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    tool_router.TOOL_CONFIG["PATENT_SEARCH"]["max_calls"] = 5
    monkeypatch.setattr(uspto_patents, "http_json", lambda *a, **k: {"results": []})
    tool_router.call_tool("tester", "patent_search", {"query": "x"})
    assert any(ev.get("tool") == "patent_search" for ev in tool_router.get_provenance())


def test_budget_downgrade(monkeypatch, tmp_path):
    _allow()
    monkeypatch.setenv("DRRD_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(uspto_patents, "http_json", lambda *a, **k: {"results": []})
    budget = {"max_tool_calls": 1}
    tool_router.call_tool("tester", "patent_search", {"query": "y1"}, budget=budget)
    out = tool_router.call_tool("tester", "patent_search", {"query": "y2"}, budget=budget)
    assert out["ok"] is False
