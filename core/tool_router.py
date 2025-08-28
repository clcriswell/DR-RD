"""In-process tool router with provenance logging and allowlists."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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


def call_tool(agent: str, tool_name: str, params: Dict[str, Any]) -> Any:
    if tool_name not in _REGISTRY:
        raise KeyError(f"Tool {tool_name} not registered")
    if tool_name not in _ALLOWLIST.get(agent, set()):
        raise PermissionError(f"Tool {tool_name} not allowed for {agent}")
    meta = _REGISTRY[tool_name]
    cfg = TOOL_CONFIG.get(meta.config_key, {})
    if not cfg.get("enabled", True):
        raise ValueError(f"Tool {tool_name} disabled")
    max_calls = cfg.get("max_calls")
    if max_calls is not None and meta.calls >= int(max_calls):
        raise ValueError("max_calls exceeded")
    start = provenance.start_span()
    result = meta.fn(**params)
    elapsed_ms = provenance.end_span(start)
    meta.calls += 1
    args_digest = _hash_dict(params)
    out_digest = _hash_dict(result if isinstance(result, dict) else {"result": result})
    provenance.record_tool_provenance(agent, tool_name, args_digest, out_digest, None, elapsed_ms)
    max_runtime = cfg.get("max_runtime_ms")
    if max_runtime is not None and elapsed_ms > int(max_runtime):
        raise TimeoutError("max_runtime_ms exceeded")
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
