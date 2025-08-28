from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


@dataclass
class SimulationSpec:
    """Specification for running a simulation."""

    id: str
    domain: str
    inputs: Dict[str, Any]
    budget_hint: Optional[str] = None
    seed: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class SimulationResult:
    """Structured result returned by simulators."""

    ok: bool
    metrics: Dict[str, Any]
    findings: List[str]
    artifacts: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    cost_summary: Optional[Dict[str, Any]] = None
    spans: Optional[List[Dict[str, Any]]] = None


class Simulator(ABC):
    """Abstract simulator interface."""

    @abstractmethod
    def run(self, spec: SimulationSpec, budget: Dict[str, Any]) -> SimulationResult:
        raise NotImplementedError
