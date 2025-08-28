"""In-process tool router with provenance logging and allowlists."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import time

import yaml

from core import provenance
from dr_rd.tools import (
    analyze_image,
    analyze_video,
    apply_patch,
    build_requirements_matrix,
    calc_unit_economics,
    classify_defects,
    compute_test_coverage,
    lookup_materials,
    monte_carlo,
    npv,
    plan_patch,
    read_repo,
    simulate,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "tools.yaml"
with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
    TOOL_CONFIG = yaml.safe_load(fh) or {}


@dataclass
class ToolMeta:
    fn: Callable
    config_key: str
    module_path: str
    input_schema: Optional[dict] = None
    calls: int = 0


_REGISTRY: Dict[str, ToolMeta] = {}
_ALLOWLIST: Dict[str, set[str]] = defaultdict(set)


def register_tool(
    name: str, fn: Callable, config_key: str, input_schema: Optional[dict] = None
) -> None:
    _REGISTRY[name] = ToolMeta(
        fn=fn,
        config_key=config_key,
        module_path=f"{fn.__module__}.{fn.__name__}",
        input_schema=input_schema,
    )


def allow_tools(agent: str, tools: list[str]) -> None:
    _ALLOWLIST[agent].update(tools)


def _hash_dict(d: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


def call_tool(agent: str, tool_name: str, params: Dict[str, Any], budget: Optional[Dict[str, Any]] = None) -> Any:
    if tool_name not in _REGISTRY:
        raise KeyError(f"Tool {tool_name} not registered")
    if tool_name not in _ALLOWLIST.get(agent, set()):
        raise PermissionError(f"Tool {tool_name} not allowed for {agent}")
    meta = _REGISTRY[tool_name]
    cfg = TOOL_CONFIG.get(meta.config_key, {})
    if not cfg.get("enabled", True):
        raise ValueError(f"Tool {tool_name} disabled")
    max_calls = cfg.get("max_calls")
    if budget and budget.get("max_tool_calls") is not None:
        max_calls = min(int(max_calls or 1e9), int(budget["max_tool_calls"]))
    if max_calls is not None and meta.calls >= int(max_calls):
        return {"ok": False, "error": "max_tool_calls exceeded"}
    span_id = provenance.start_span(tool_name, {"agent": agent, "tool": tool_name, "args_digest": _hash_dict(params)})
    start = time.time()
    result = meta.fn(**params)
    elapsed_ms = int((time.time() - start) * 1000)
    provenance.end_span(span_id, meta={"output_digest": _hash_dict(result if isinstance(result, dict) else {"result": result}), "elapsed_ms": elapsed_ms})
    meta.calls += 1
    max_runtime = cfg.get("max_runtime_ms")
    if budget and budget.get("max_runtime_ms") is not None:
        max_runtime = min(int(max_runtime or 1e9), int(budget["max_runtime_ms"]))
    if max_runtime is not None and elapsed_ms > int(max_runtime):
        return {"ok": False, "error": "max_runtime_ms exceeded"}
    return result


def get_provenance() -> list[Dict[str, Any]]:
    return provenance.get_events()


# Register built-in tools on import

register_tool("read_repo", read_repo, "CODE_IO")
register_tool("plan_patch", plan_patch, "CODE_IO")
register_tool("apply_patch", apply_patch, "CODE_IO")
register_tool("simulate", simulate, "SIMULATION")
register_tool("analyze_image", analyze_image, "VISION")
register_tool("analyze_video", analyze_video, "VISION")
register_tool("lookup_materials", lookup_materials, "MATERIALS_DB")
register_tool("build_requirements_matrix", build_requirements_matrix, "QA_CHECKS")
register_tool("compute_test_coverage", compute_test_coverage, "QA_CHECKS")
register_tool("classify_defects", classify_defects, "QA_CHECKS")
register_tool("calc_unit_economics", calc_unit_economics, "FINANCE")
register_tool("npv", npv, "FINANCE")
register_tool("monte_carlo", monte_carlo, "FINANCE")
