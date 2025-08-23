from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseEvaluator(ABC):
    """Evaluator extension point."""

    @abstractmethod
    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Return evaluation data for the given state."""

    def weight(self) -> float:  # pragma: no cover - default implementation
        return 1.0

    def name(self) -> str:  # pragma: no cover - default implementation
        return self.__class__.__name__


class BasePlannerStrategy(ABC):
    """Planning strategy extension point."""

    @abstractmethod
    def plan(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Produce a list of tasks for the given state."""


class BaseSimulator(ABC):
    """Simulation extension point."""

    @abstractmethod
    def run(
        self, design: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a simulation and return the result."""


class BaseMetaAgent(ABC):
    """Meta agent extension point."""

    @abstractmethod
    def reflect(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adjust strategy based on execution history."""
