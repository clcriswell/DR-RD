"""Typed models for provenance tracing and run metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RunMeta:
    """Metadata about a single execution run.

    Attributes mirror the lightweight information stored next to provenance
    spans.  Only primitive JSON serialisable types are used so that the model can
    be easily persisted with :mod:`json`.
    """

    run_id: str
    started_at: str
    flags: Dict[str, Any] = field(default_factory=dict)
    budgets: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """A single timed span within a run."""

    id: str
    parent_id: Optional[str]
    agent: Optional[str]
    tool: Optional[str]
    event: Optional[str]
    meta: Dict[str, Any] = field(default_factory=dict)
    t_start: float = 0.0
    t_end: Optional[float] = None
    duration_ms: Optional[int] = None
    tokens: Optional[int] = None
    ok: bool = True
    error_code: Optional[str] = None
    error_msg_hash: Optional[str] = None


@dataclass
class RouteDecisionMeta:
    """Placeholder for route decision details."""

    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalMeta:
    """Placeholder for retrieval related details."""

    info: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "RunMeta",
    "Span",
    "RouteDecisionMeta",
    "RetrievalMeta",
]
