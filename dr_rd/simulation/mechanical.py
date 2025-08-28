from __future__ import annotations

from typing import Dict, Any
import math

from .interfaces import SimulationSpec, SimulationResult, Simulator


class MechanicalSimulator(Simulator):
    """Very small deterministic beam deflection simulator."""

    def run(self, spec: SimulationSpec, budget: Dict[str, Any]) -> SimulationResult:
        inp = spec.inputs
        length = float(inp.get("length", 1.0))
        width = float(inp.get("width", 1.0))
        height = float(inp.get("height", 1.0))
        density = float(inp.get("density", 1.0))
        load = float(inp.get("load", 1.0))
        volume = length * width * height
        mass = density * volume
        inertia = (width * height**3) / 12.0
        deflection = (load * length**3) / (3 * 1e5 * inertia)
        safety = (1e5 * inertia) / max(load * length, 1e-6)
        metrics = {
            "mass": mass,
            "deflection": deflection,
            "safety_factor": safety,
        }
        return SimulationResult(
            ok=True,
            metrics=metrics,
            findings=["beam_simulated"],
            artifacts=[],
            sources=[],
            cost_summary={"token_est": 0, "tool_runtime_ms": 0},
            spans=[],
        )
