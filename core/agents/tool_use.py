from __future__ import annotations

from collections import defaultdict, deque
import time
from typing import Any, Optional, Dict

from core import tool_router


class ToolUseMixin:
    """Mixin providing safe tool execution for agents."""

    _error_log: Dict[str, deque[float]] = defaultdict(deque)

    def run_tool(self, tool_name: str, params: dict) -> Any:
        """Invoke a registered tool with circuit breaker checks."""
        if tool_name not in tool_router._REGISTRY:
            raise KeyError(f"Tool {tool_name} not registered")
        _, key = tool_router._REGISTRY[tool_name]
        cfg = tool_router.TOOL_CONFIG.get(key, {})
        circuit = cfg.get("circuit", {})
        max_errors = int(circuit.get("max_errors", 3))
        window_s = int(circuit.get("window_s", 60))
        dq = self._error_log[tool_name]
        now = time.time()
        while dq and now - dq[0] > window_s:
            dq.popleft()
        if len(dq) >= max_errors:
            raise RuntimeError("circuit_open")
        if not cfg.get("enabled", False):
            raise ValueError(f"Tool {tool_name} disabled")
        try:
            return tool_router.call_tool(self.name, tool_name, params)
        except Exception:
            dq.append(time.time())
            raise


def should_use_tool(task: dict) -> Optional[dict]:
    """Inspect a task and infer an explicit tool request if present."""
    req = task.get("tool_request")
    if isinstance(req, dict) and "tool" in req and isinstance(req.get("params"), dict):
        return req
    desc = (task.get("description") or "").lower()
    code_kw = ["read code", "diff", "patch", "repo", "glob", "unified diff"]
    sim_kw = ["simulate", "digital twin", "monte carlo", "sweep"]
    vis_kw = ["image", "video", "ocr", "classify", "detect"]
    if any(k in desc for k in code_kw):
        return {"tool": "read_repo", "params": {}}
    if any(k in desc for k in sim_kw):
        return {"tool": "simulate", "params": {}}
    if any(k in desc for k in vis_kw):
        if "video" in desc:
            return {"tool": "analyze_video", "params": {}}
        return {"tool": "analyze_image", "params": {}}
    return None
