"""Trace schema definitions."""
from __future__ import annotations

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    """Unified representation for a single trace event."""

    ts: float
    node: str
    phase: str
    task_id: Optional[str] = None
    agent: Optional[str] = None
    tool: Optional[str] = None
    score: Optional[float] = None
    attempt: Optional[int] = None
    duration_s: Optional[float] = None
    tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    meta: Dict[str, object] = Field(default_factory=dict)


class TraceBundle(BaseModel):
    """Container for a list of :class:`TraceEvent` objects."""

    events: List[TraceEvent] = Field(default_factory=list)
