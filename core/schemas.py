from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ScopeNote(BaseModel):
    idea: str
    constraints: list[str]
    time_budget_hours: Optional[float] = None
    cost_budget_usd: Optional[float] = None
    risk_posture: Literal["low", "medium", "high"]
    redaction_rules: list[str]


class ConceptBrief(BaseModel):
    problem: str
    value: str
    users: list[str]
    success_metrics: list[str]
    risks: list[str]
    cost_range: str


class RoleCard(BaseModel):
    role: str
    responsibilities: list[str]
    inputs: list[str]
    outputs: list[str]


class TaskSpec(BaseModel):
    role: str
    task: str
    inputs: Optional[dict[str, Any]] = None
    stop_rules: Optional[list[str]] = None


__all__ = [
    "ScopeNote",
    "ConceptBrief",
    "RoleCard",
    "TaskSpec",
]
