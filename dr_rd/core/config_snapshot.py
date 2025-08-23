from __future__ import annotations

from typing import Any, Dict


def _maybe(cfg: Dict[str, Any], *keys: str) -> Any:
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def build_resolved_config_snapshot(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return a redacted configuration snapshot for logging."""
    models = cfg.get("models", {}) if isinstance(cfg.get("models"), dict) else {}
    snapshot: Dict[str, Any] = {
        "mode": cfg.get("mode"),
        "planner_model": models.get("plan"),
        "exec_model": models.get("exec"),
        "synth_model": models.get("synth"),
        "rag_enabled": bool(cfg.get("rag_enabled")),
        "rag_top_k": cfg.get("rag_top_k"),
        "live_search_enabled": bool(cfg.get("live_search_enabled")),
        "live_search_backend": cfg.get("live_search_backend"),
    }
    if "live_search_max_calls" in cfg:
        snapshot["web_search_max_calls"] = cfg.get("live_search_max_calls")
        snapshot["web_search_calls_used"] = cfg.get("web_search_calls_used", 0)
    # Budget caps
    budget = cfg.get("budget") if isinstance(cfg.get("budget"), dict) else {}
    caps = {
        k: budget.get(k) for k in ["max_tokens", "max_cost_usd", "target_cost_usd"] if k in budget
    }
    if caps:
        snapshot["budget_caps"] = caps
    # Vector index
    if "vector_index_present" in cfg:
        snapshot["vector_index_present"] = bool(cfg.get("vector_index_present"))
        vpath = _maybe(cfg, "vector_index_path") or _maybe(cfg, "vector_index")
    else:
        vpath = _maybe(cfg, "vector_index_path") or _maybe(cfg, "vector_index")
        snapshot["vector_index_present"] = bool(vpath)
    if vpath:
        from pathlib import Path

        snapshot["vector_index_path"] = Path(str(vpath)).name
    if "vector_index_source" in cfg:
        snapshot["vector_index_source"] = cfg.get("vector_index_source")
    if "faiss_bootstrap_mode" in cfg:
        snapshot["faiss_bootstrap_mode"] = cfg.get("faiss_bootstrap_mode")
    if "vector_doc_count" in cfg:
        snapshot["vector_doc_count"] = cfg.get("vector_doc_count")
    return {k: v for k, v in snapshot.items() if v is not None}
