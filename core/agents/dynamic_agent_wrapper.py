"""Wrapper exposing DynamicAgent under core.agents namespace."""

from __future__ import annotations

from typing import Any, Dict

from dr_rd.agents.dynamic_agent import DynamicAgent


class DynamicAgentWrapper:
    def __init__(self, model: str) -> None:
        self.impl = DynamicAgent(model)

    def run(self, spec: Dict[str, Any]) -> Any:
        data, _schema = self.impl.run(spec)
        return data
