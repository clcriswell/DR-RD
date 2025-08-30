"""Serialization helpers for run configuration lockfiles."""

from __future__ import annotations

import time
from typing import Any, Mapping

SCHEMA_VERSION = 1


def _validate_str(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _validate_list_str(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"{field} must be a list of strings")
    return value


def _validate_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return dict(value)


def to_lockfile(cfg: Mapping[str, Any]) -> dict:
    """
    Returns a dict with:
      {"schema": SCHEMA_VERSION, "created_at": ts,
       "inputs": {idea, mode, budget_limit_usd, max_tokens, knowledge_sources, advanced, seed}}
    """
    idea = _validate_str(cfg.get("idea", ""), "idea")[:200]
    mode = _validate_str(cfg.get("mode", "standard"), "mode")
    budget_limit = cfg.get("budget_limit_usd")
    if budget_limit is not None:
        budget_limit = float(budget_limit)
    max_tokens = cfg.get("max_tokens")
    if max_tokens is not None:
        max_tokens = int(max_tokens)
    ks = cfg.get("knowledge_sources") or []
    ks = _validate_list_str(ks, "knowledge_sources")
    adv = cfg.get("advanced") or {}
    if not isinstance(adv, Mapping):
        raise ValueError("advanced must be a mapping")
    seed = cfg.get("seed")
    if seed is not None:
        seed = int(seed)
    inputs = {
        "idea": idea,
        "mode": mode,
        "budget_limit_usd": budget_limit,
        "max_tokens": max_tokens,
        "knowledge_sources": ks,
        "advanced": dict(adv),
        "seed": seed,
    }
    return {"schema": SCHEMA_VERSION, "created_at": int(time.time()), "inputs": inputs}


def from_lockfile(obj: Mapping[str, Any]) -> dict:
    """Validate types, drop unknowns, return normalized dict suitable for RunConfig adapter."""
    if obj.get("schema") != SCHEMA_VERSION:
        raise ValueError("unsupported schema version")
    inputs = obj.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("inputs must be a mapping")
    idea = _validate_str(inputs.get("idea", ""), "idea")[:200]
    mode = _validate_str(inputs.get("mode", "standard"), "mode")
    budget_limit = inputs.get("budget_limit_usd")
    if budget_limit is not None:
        budget_limit = float(budget_limit)
    max_tokens = inputs.get("max_tokens")
    if max_tokens is not None:
        max_tokens = int(max_tokens)
    ks = inputs.get("knowledge_sources") or []
    ks = _validate_list_str(ks, "knowledge_sources")
    adv = inputs.get("advanced") or {}
    adv = _validate_mapping(adv, "advanced")
    seed = inputs.get("seed")
    if seed is not None:
        seed = int(seed)
    return {
        "idea": idea,
        "mode": mode,
        "budget_limit_usd": budget_limit,
        "max_tokens": max_tokens,
        "knowledge_sources": ks,
        "advanced": adv,
        "seed": seed,
    }
