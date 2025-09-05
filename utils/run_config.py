from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List

import streamlit as st


@dataclass(frozen=True)
class RunConfig:
    """Typed configuration for a single run."""

    idea: str = ""
    mode: str = "standard"
    rag_enabled: bool = False
    live_search_enabled: bool = False
    enforce_budget: bool = False
    budget_limit_usd: float | None = None
    max_tokens: int | None = None
    # Selected knowledge item IDs from built-ins and uploads
    knowledge_sources: List[str] = field(default_factory=list)
    show_agent_trace: bool = False
    verbose_planner: bool = False
    auto_export_trace: bool = False
    auto_export_report: bool = False
    pseudonymize_to_model: bool = True
    advanced: Dict[str, Any] = field(default_factory=dict)


def defaults() -> RunConfig:
    """Return default run configuration."""

    from .prefs import merge_defaults

    base = asdict(RunConfig())
    merged = merge_defaults(base)
    return RunConfig(**merged)


def from_session() -> RunConfig:
    """Build a RunConfig from ``st.session_state``."""

    base = defaults()
    data = {}
    for f in fields(RunConfig):
        data[f.name] = st.session_state.get(f.name, getattr(base, f.name))
    return RunConfig(**data)


def to_session(cfg: RunConfig | None = None) -> None:
    """Seed ``st.session_state`` with values from ``cfg`` if missing."""

    if cfg is None:
        cfg = defaults()
    for f in fields(RunConfig):
        st.session_state.setdefault(f.name, getattr(cfg, f.name))


def to_orchestrator_kwargs(cfg: RunConfig) -> Dict[str, Any]:
    """Convert a ``RunConfig`` into kwargs for orchestrators."""

    kwargs: Dict[str, Any] = {
        "idea": cfg.idea,
        "rag": cfg.rag_enabled,
        "live": cfg.live_search_enabled,
        "budget": cfg.enforce_budget,
        "budget_limit_usd": cfg.budget_limit_usd,
        "max_tokens": cfg.max_tokens,
        "knowledge_sources": list(cfg.knowledge_sources),
        "pseudonymize_to_model": cfg.pseudonymize_to_model,
    }
    kwargs["mode"] = cfg.mode
    kwargs.update(cfg.advanced)
    return kwargs
