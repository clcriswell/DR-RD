from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def _now() -> str:
    """Return current UTC timestamp in ISO format with trailing Z."""
    return datetime.utcnow().isoformat() + "Z"


class TraceEvent(BaseModel):
    type: Literal["route", "call", "retry", "validate", "save_evidence", "complete"]
    ts: str = Field(default_factory=_now)
    meta: Dict[str, Any] = Field(default_factory=dict)


class AgentTraceItem(BaseModel):
    project_id: str
    task_id: str
    step_no: int
    role: str
    title: str = ""
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    quotes: List[Any] = Field(default_factory=list)
    citations: List[Any] = Field(default_factory=list)
    finding: str = ""
    raw_json: Dict[str, Any] = Field(default_factory=dict)
    events: List[TraceEvent] = Field(default_factory=list)
    ts_start: str = Field(default_factory=_now)
    ts_end: Optional[str] = None


class AgentTraceCollector:
    """Collect AgentTraceItem entries during plan execution."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.items: List[AgentTraceItem] = []

    def start_item(self, task: Dict[str, Any], role: str, model: str) -> int:
        item = AgentTraceItem(
            project_id=self.project_id,
            task_id=task.get("id", ""),
            step_no=len(self.items) + 1,
            role=role,
            title=task.get("title", ""),
            model=model,
        )
        self.items.append(item)
        return len(self.items) - 1

    def append_event(self, handle: int, type: str, meta: Dict[str, Any]) -> None:
        self.items[handle].events.append(TraceEvent(type=type, meta=meta))

    def finalize_item(
        self,
        handle: int,
        finding: str,
        raw_json: Dict[str, Any],
        tokens_in: int,
        tokens_out: int,
        cost: float,
        quotes: List[Any],
        citations: List[Any],
        ts_end: Optional[str] = None,
    ) -> None:
        item = self.items[handle]
        item.finding = finding
        item.raw_json = raw_json
        item.tokens_in = tokens_in
        item.tokens_out = tokens_out
        item.cost_usd = cost
        item.quotes = quotes
        item.citations = citations
        item.ts_end = ts_end or _now()
        self.append_event(handle, "complete", {})

    def as_dicts(self) -> List[Dict[str, Any]]:
        return [i.model_dump() for i in self.items]
