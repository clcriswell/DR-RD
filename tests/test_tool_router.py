import pytest
from core import tool_router


def test_unregistered_tool_raises():
    with pytest.raises(KeyError):
        tool_router.call_tool("agent", "unknown", {})


def test_registered_tool_provenance():
    result = tool_router.call_tool("agent", "plan_patch", {"diff_spec": "foo"})
    assert result == "foo"
    prov = tool_router.get_provenance()
    assert any(p["tool"] == "plan_patch" for p in prov)
