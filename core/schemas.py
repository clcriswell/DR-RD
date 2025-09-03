from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class ScopeNote(BaseModel):
    """Metadata captured from the intake UI about the project scope."""

    idea: str
    constraints: list[str]
    time_budget_hours: float | None = None
    cost_budget_usd: float | None = None
    risk_posture: Literal["low", "medium", "high"]
    redaction_rules: list[str] | None = None


class Task(BaseModel):
    """Single task item produced by the planner."""

    id: str
    title: str = Field(
        min_length=1, validation_alias=AliasChoices("title", "role", "name")
    )
    summary: str = Field(
        min_length=1,
        validation_alias=AliasChoices("summary", "objective", "description", "goal"),
    )
    description: str = Field(
        min_length=1, validation_alias=AliasChoices("description", "detail", "details")
    )
    role: str = Field(min_length=1)
    inputs: dict[str, Any] | None = None
    dependencies: list[str] = Field(default_factory=list)
    stop_rules: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tool_request: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("title", "summary", "description", "role")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class Plan(BaseModel):
    """Planner response schema."""

    tasks: list[Task] = Field(min_length=1)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


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
    inputs: dict[str, Any] | None = None
    stop_rules: list[str] | None = None


__all__ = [
    "ScopeNote",
    "Task",
    "Plan",
    "ConceptBrief",
    "RoleCard",
    "TaskSpec",
]
