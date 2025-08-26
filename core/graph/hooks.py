from __future__ import annotations

import time
from typing import Optional

from .state import GraphState


def _append_trace(state: GraphState, event: str, node: str, task_id: Optional[str] = None) -> None:
    state.trace.append({"event": event, "node": node, "ts": time.time(), "task_id": task_id})


def node_start(state: GraphState, node: str, task_id: Optional[str] = None) -> None:
    _append_trace(state, "start", node, task_id)


def node_end(state: GraphState, node: str, task_id: Optional[str] = None) -> None:
    _append_trace(state, "end", node, task_id)
