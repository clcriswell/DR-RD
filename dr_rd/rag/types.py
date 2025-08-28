"""Lightweight data models for retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class QuerySpec:
    role: str
    task: str
    query: str
    filters: Dict[str, Any] | None = None
    domain: Optional[str] = None
    top_k: int = 5
    policy: str = "LIGHT"
    budget_hint: str | None = None


@dataclass
class Doc:
    id: str
    url: str
    title: str
    domain: str
    published_at: Optional[str]
    text: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    doc: Doc
    score: float
    reasons: List[str] = field(default_factory=list)
    rank: int = 0
    components: Dict[str, float] = field(default_factory=dict)


@dataclass
class ContextBundle:
    hits: List[Hit]
    sources: List[Dict[str, Any]]
    tokens_est: int
