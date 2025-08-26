from __future__ import annotations

from typing import List
try:  # pragma: no cover - runtime import may vary
    from pydantic import BaseModel, Field, field_validator
except Exception:  # pydantic not available or old version
    try:
        from pydantic import BaseModel, Field, validator as field_validator
    except Exception:  # very minimal fallback for tooling
        class BaseModel:  # type: ignore
            pass

        def Field(**kwargs):  # type: ignore
            return None

        def field_validator(*args, **kwargs):  # type: ignore
            def _wrap(fn):
                return fn

            return _wrap


class RoleSummary(BaseModel):
    """Summary of an individual agent's findings."""

    role: str
    bullets: List[str] = Field(default_factory=list)

    @field_validator("bullets")
    @classmethod
    def _max_five(cls, v: List[str]) -> List[str]:
        if len(v) > 5:
            raise ValueError("bullets cannot exceed 5 items")
        return v


class IntegratedSummary(BaseModel):
    """Combined view across all roles including contradictions."""

    plan_summary: str
    key_findings: List[str]
    contradictions: List[str] = Field(default_factory=list)
