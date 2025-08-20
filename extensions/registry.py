from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from .abcs import BaseEvaluator, BasePlannerStrategy, BaseSimulator, BaseMetaAgent


class Registry:
    """Simple class registry."""

    def __init__(self) -> None:
        self._items: Dict[str, Type[Any]] = {}

    def register(self, name: str, cls: Type[Any]) -> None:
        self._items[name] = cls

    def get(self, name: str) -> Optional[Type[Any]]:
        return self._items.get(name)

    def list(self) -> List[str]:
        return list(self._items.keys())


EvaluatorRegistry = Registry()
PlannerStrategyRegistry = Registry()
SimulatorRegistry = Registry()
MetaAgentRegistry = Registry()
