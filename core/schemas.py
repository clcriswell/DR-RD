from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ScopeNote(BaseModel):
    """Metadata captured from the intake UI about the project scope."""

    idea: str
    constraints: List[str]
    time_budget_hours: Optional[float] = None
    cost_budget_usd: Optional[float] = None
    risk_posture: Literal["low", "medium", "high"]
    redaction_rules: Optional[List[str]] = None


class Task(BaseModel):
    """Single task item produced by the planner."""

    id: str
    role: str
    title: str
    summary: str
    description: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)
    stop_rules: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    tool_request: Optional[Dict[str, Any]] = None


class Plan(BaseModel):
    """Planner response schema."""

    tasks: List[Task] = Field(min_length=1)


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
    "Task",
    "Plan",
    "ConceptBrief",
    "RoleCard",
    "TaskSpec",
]
