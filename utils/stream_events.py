from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any

EventKind = Literal[
    "phase_start",
    "phase_end",
    "step_start",
    "step_end",
    "token",
    "message",
    "summary",
    "error",
    "usage_delta",
    "done",
]


@dataclass(frozen=True)
class Event:
    kind: EventKind
    phase: Optional[str] = None
    step_id: Optional[str] = None
    text: Optional[str] = None
    meta: Dict[str, Any] | None = None


def merge_text(prev: str | None, piece: str | None) -> str:
    return (prev or "") + (piece or "")


def is_terminal(e: "Event") -> bool:
    return e.kind in {"error", "done"}


__all__ = ["Event", "EventKind", "merge_text", "is_terminal"]
