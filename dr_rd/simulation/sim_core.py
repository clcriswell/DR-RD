from __future__ import annotations

from typing import Dict

from .interfaces import SimulationSpec, SimulationResult, Simulator

_REGISTRY: Dict[str, Simulator] = {}


def register(domain: str, simulator: Simulator) -> None:
    """Register a simulator implementation for a domain."""
    _REGISTRY[domain] = simulator


def run(domain: str, spec: SimulationSpec, budget: Dict[str, any]) -> SimulationResult:
    if domain not in _REGISTRY:
        raise KeyError(f"Simulator for domain '{domain}' not registered")
    return _REGISTRY[domain].run(spec, budget)
