import pytest
from core import tool_router
from collections import defaultdict, deque


def failing_tool(**kwargs):
    raise RuntimeError("boom")


def test_circuit_breaker(monkeypatch):
    monkeypatch.setitem(tool_router._REGISTRY, "fail", (failing_tool, "CODE_IO"))
    monkeypatch.setitem(
        tool_router.TOOL_CONFIG,
        "CODE_IO",
        {"enabled": True, "circuit": {"max_errors": 2, "window_s": 60}},
    )
    monkeypatch.setattr(tool_router, "_ERROR_LOG", defaultdict(deque))
    for _ in range(2):
        with pytest.raises(RuntimeError):
            tool_router.call_tool("agent", "fail", {})
    with pytest.raises(RuntimeError) as exc:
        tool_router.call_tool("agent", "fail", {})
    assert "circuit_open" in str(exc.value)
