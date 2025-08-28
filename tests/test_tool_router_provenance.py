from core import tool_router


def test_provenance_logging():
    tool_router.allow_tools("Tester", ["lookup_materials"])
    tool_router.call_tool("Tester", "lookup_materials", {"query": "steel"})
    events = tool_router.get_provenance()
    assert events and events[-1]["tool"] == "lookup_materials"
    assert events[-1]["elapsed_ms"] >= 0
    assert len(events[-1]["args_digest"]) > 10
