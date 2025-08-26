from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GraphTask(BaseModel):
    """Single task within the LangGraph orchestration."""

    id: str
    role: Optional[str] = None
    title: str
    description: str
    stop_rules: Optional[List[str]] = None
    tool_request: Optional[Dict[str, Any]] = None


class GraphState(BaseModel):
    """State container passed between LangGraph nodes."""

    idea: str
    constraints: List[str]
    risk_posture: str
    tasks: List[GraphTask] = []
    cursor: int = 0
    answers: Dict[str, Any] = {}
    trace: List[Dict[str, Any]] = []
    tool_trace: List[Dict[str, Any]] = []
    retrieved: Dict[str, List[Dict[str, Any]]] = {}
    final: Optional[str] = None
