"""In-process tool router with provenance logging."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Any, Dict
from collections import defaultdict, deque
import time
import json
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "tools.yaml"
with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
    TOOL_CONFIG = yaml.safe_load(fh) or {}

_REGISTRY: Dict[str, tuple[Callable, str]] = {}
_PROVENANCE: list[Dict[str, Any]] = []
_ERROR_LOG: Dict[str, deque[float]] = defaultdict(deque)


def register_tool(name: str, fn: Callable, config_key: str) -> None:
    _REGISTRY[name] = (fn, config_key)


def _hash_dict(d: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def call_tool(agent: str, tool_name: str, params: Dict[str, Any]) -> Any:
    if tool_name not in _REGISTRY:
        raise KeyError(f"Tool {tool_name} not registered")
    fn, key = _REGISTRY[tool_name]
    cfg = TOOL_CONFIG.get(key, {})
    if not cfg.get("enabled", False):
        raise ValueError(f"Tool {tool_name} disabled")

    circuit = cfg.get("circuit", {})
    max_errors = int(circuit.get("max_errors", 3))
    window_s = int(circuit.get("window_s", 60))
    dq = _ERROR_LOG[tool_name]
    now = time.time()
    while dq and now - dq[0] > window_s:
        dq.popleft()
    if len(dq) >= max_errors:
        raise RuntimeError("circuit_open")

    start = time.time()
    if key == "CODE_IO":
        max_files = cfg.get("max_files", 0)
        if tool_name == "apply_patch":
            diff = params.get("diff", "")
            files = [line[6:] for line in diff.splitlines() if line.startswith("+++ b/")]
            if max_files and len(files) > max_files:
                raise ValueError("Too many files in patch")

    try:
        result = fn(**params)
    except Exception:
        dq.append(time.time())
        raise

    if key == "CODE_IO" and tool_name == "read_repo":
        max_files = cfg.get("max_files", 0)
        truncated = False
        if isinstance(result, list) and max_files and len(result) > max_files:
            result = result[:max_files]
            truncated = True
        result = {"results": result, "truncated": truncated}
    wall = time.time() - start
    prov = {
        "agent": agent,
        "tool": tool_name,
        "inputs_hash": _hash_dict(params),
        "outputs_digest": hashlib.sha256(str(result).encode()).hexdigest()[:12],
        "tokens": 0,
        "wall_time": wall,
    }
    _PROVENANCE.append(prov)
    return result


def get_provenance() -> list[Dict[str, Any]]:
    return list(_PROVENANCE)


# Register built-in tools on import
from dr_rd.tools import (
    read_repo,
    plan_patch,
    apply_patch,
    analyze_image,
    analyze_video,
)
from dr_rd.tools.simulations import simulate

register_tool("read_repo", read_repo, "CODE_IO")
register_tool("plan_patch", plan_patch, "CODE_IO")
register_tool("apply_patch", apply_patch, "CODE_IO")
register_tool("simulate", simulate, "SIMULATION")
register_tool("analyze_image", analyze_image, "VISION")
register_tool("analyze_video", analyze_video, "VISION")
