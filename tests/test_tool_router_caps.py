import time
from core import tool_router


def dummy_tool(delay: float = 0.0):
    if delay:
        time.sleep(delay)
    return {"ok": True}


def test_tool_caps(monkeypatch):
    tool_router.register_tool("dummy", dummy_tool, "CODE_IO")
    tool_router.allow_tools("Agent", ["dummy"])
    budget = {"max_tool_calls": 1, "max_runtime_ms": 10}
    res1 = tool_router.call_tool("Agent", "dummy", {}, budget)
    assert res1["ok"]
    res2 = tool_router.call_tool("Agent", "dummy", {}, budget)
    assert res2["error"] == "max_tool_calls exceeded"
    slow_budget = {"max_tool_calls": 5, "max_runtime_ms": 0}
    res3 = tool_router.call_tool("Agent", "dummy", {"delay": 0.01}, slow_budget)
    assert res3["error"] == "max_runtime_ms exceeded"
