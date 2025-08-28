from __future__ import annotations

from typing import Dict, Any

from .interfaces import SimulationSpec, SimulationResult, Simulator
from dr_rd.tools.materials_db import lookup_materials


class MaterialsSimulator(Simulator):
    """Trade-off simulator using sample materials database."""

    def run(self, spec: SimulationSpec, budget: Dict[str, Any]) -> SimulationResult:
        query = str(spec.inputs.get("query", ""))
        options = lookup_materials(query)
        metrics = {"options_considered": len(options)}
        findings = [o["name"] for o in options]
        return SimulationResult(
            ok=True,
            metrics=metrics,
            findings=findings,
            artifacts=[],
            sources=[],
            cost_summary={"token_est": 0, "tool_runtime_ms": 0},
            spans=[],
        )
