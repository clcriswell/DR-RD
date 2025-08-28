"""In-process tool router with provenance logging and allowlists."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import jsonschema
import yaml

from config import feature_flags
from core import provenance
from dr_rd.cache.file_cache import FileCache
from dr_rd.connectors.fda_devices import search_devices
from dr_rd.connectors.govinfo_cfr import lookup_cfr
from dr_rd.connectors.regulations_gov import fetch_document, search_documents
from dr_rd.connectors.uspto_patents import fetch_patent, search_patents
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
    output_schema: Optional[dict] = None
    caps: Dict[str, Any] | None = None
    cost_tags: Dict[str, Any] | None = None
    calls: int = 0


_REGISTRY: Dict[str, ToolMeta] = {}
_ALLOWLIST: Dict[str, set[str]] = defaultdict(set)
_CACHE = FileCache(Path(".cache") / "tools")


def register_tool(
    name: str,
    fn: Callable,
    config_key: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    caps: Optional[Dict[str, Any]] = None,
    cost_tags: Optional[Dict[str, Any]] = None,
) -> None:
    _REGISTRY[name] = ToolMeta(
        fn=fn,
        config_key=config_key,
        module_path=f"{fn.__module__}.{fn.__name__}",
        input_schema=input_schema,
        output_schema=output_schema,
        caps=caps,
        cost_tags=cost_tags,
    )


def allow_tools(agent: str, tools: list[str]) -> None:
    _ALLOWLIST[agent].update(tools)


def _hash_dict(d: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


def call_tool(
    agent: str, tool_name: str, params: Dict[str, Any], budget: Optional[Dict[str, Any]] = None
) -> Any:
    if tool_name not in _REGISTRY:
        raise KeyError(f"Tool {tool_name} not registered")
    if tool_name not in _ALLOWLIST.get(agent, set()):
        raise PermissionError(f"Tool {tool_name} not allowed for {agent}")
    meta = _REGISTRY[tool_name]
    cfg = TOOL_CONFIG.get(meta.config_key, {})
    if not cfg.get("enabled", True):
        raise ValueError(f"Tool {tool_name} disabled")
    if meta.input_schema:
        jsonschema.validate(params, meta.input_schema)
    max_calls = cfg.get("max_calls")
    if budget and budget.get("max_tool_calls") is not None:
        max_calls = min(int(max_calls or 1e9), int(budget["max_tool_calls"]))
    if max_calls is not None and meta.calls >= int(max_calls):
        return {"ok": False, "error": "max_tool_calls exceeded"}
    cache_ttl = cfg.get("ttl_s")
    cache_key = f"{tool_name}:{_hash_dict(params)}"
    if cache_ttl:
        cached = _CACHE.get(cache_key, cache_ttl)
        if cached is not None:
            if feature_flags.PROVENANCE_ENABLED:
                span = provenance.start_span(
                    tool_name,
                    {
                        "agent": agent,
                        "tool": tool_name,
                        "cached": True,
                        "args_digest": _hash_dict(params),
                    },
                )
                provenance.end_span(
                    span,
                    meta={"cached": True, "output_digest": _hash_dict(cached), "elapsed_ms": 0},
                )
            return cached
    span = None
    if feature_flags.PROVENANCE_ENABLED:
        span = provenance.start_span(
            tool_name, {"agent": agent, "tool": tool_name, "args_digest": _hash_dict(params)}
        )
    start = time.time()
    result = meta.fn(**params)
    elapsed_ms = int((time.time() - start) * 1000)
    if feature_flags.PROVENANCE_ENABLED and span is not None:
        provenance.end_span(
            span,
            meta={
                "output_digest": _hash_dict(
                    result if isinstance(result, dict) else {"result": result}
                ),
                "elapsed_ms": elapsed_ms,
            },
        )
    meta.calls += 1
    max_runtime = cfg.get("max_runtime_ms")
    if budget and budget.get("max_runtime_ms") is not None:
        max_runtime = min(int(max_runtime or 1e9), int(budget["max_runtime_ms"]))
    if max_runtime is not None and elapsed_ms > int(max_runtime):
        return {"ok": False, "error": "max_runtime_ms exceeded"}
    if meta.output_schema:
        jsonschema.validate(result, meta.output_schema)
    if cache_ttl:
        _CACHE.set(cache_key, result)
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

# Patent and regulatory connectors
with open(ROOT / "dr_rd" / "tooldefs" / "patent_search_v1.json", "r", encoding="utf-8") as fh:
    _patent_search_schema = json.load(fh)
with open(ROOT / "dr_rd" / "tooldefs" / "patent_fetch_v1.json", "r", encoding="utf-8") as fh:
    _patent_fetch_schema = json.load(fh)
with open(ROOT / "dr_rd" / "tooldefs" / "reg_search_v1.json", "r", encoding="utf-8") as fh:
    _reg_search_schema = json.load(fh)
with open(ROOT / "dr_rd" / "tooldefs" / "reg_fetch_v1.json", "r", encoding="utf-8") as fh:
    _reg_fetch_schema = json.load(fh)
with open(ROOT / "dr_rd" / "tooldefs" / "cfr_lookup_v1.json", "r", encoding="utf-8") as fh:
    _cfr_lookup_schema = json.load(fh)
with open(ROOT / "dr_rd" / "tooldefs" / "fda_device_search_v1.json", "r", encoding="utf-8") as fh:
    _fda_device_search_schema = json.load(fh)

register_tool(
    "patent_search",
    search_patents,
    "PATENT_SEARCH",
    input_schema=_patent_search_schema["input"],
    output_schema=_patent_search_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)
register_tool(
    "patent_fetch",
    fetch_patent,
    "PATENT_FETCH",
    input_schema=_patent_fetch_schema["input"],
    output_schema=_patent_fetch_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)
register_tool(
    "reg_search",
    search_documents,
    "REG_SEARCH",
    input_schema=_reg_search_schema["input"],
    output_schema=_reg_search_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)
register_tool(
    "reg_fetch",
    fetch_document,
    "REG_FETCH",
    input_schema=_reg_fetch_schema["input"],
    output_schema=_reg_fetch_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)
register_tool(
    "cfr_lookup",
    lookup_cfr,
    "CFR_LOOKUP",
    input_schema=_cfr_lookup_schema["input"],
    output_schema=_cfr_lookup_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)
register_tool(
    "fda_device_search",
    search_devices,
    "FDA_DEVICE_SEARCH",
    input_schema=_fda_device_search_schema["input"],
    output_schema=_fda_device_search_schema["output"],
    caps={"max_calls": 5},
    cost_tags={"network": True, "cached_ok": True},
)

__all__ = [
    "register_tool",
    "allow_tools",
    "call_tool",
    "get_provenance",
]
