from __future__ import annotations

from typing import Dict, Any

from .interfaces import SimulationSpec, SimulationResult, Simulator
from dr_rd.tools.finance import monte_carlo, npv


class FinanceSimulator(Simulator):
    """Wrap financial tools as simulation runs."""

    def run(self, spec: SimulationSpec, budget: Dict[str, Any]) -> SimulationResult:
        inp = spec.inputs
        metrics: Dict[str, Any]
        if "params" in inp:
            metrics = monte_carlo(inp.get("params", {}), trials=inp.get("trials", 100))
        else:
            metrics = {
                "npv": npv(inp.get("cash_flows", []), float(inp.get("discount_rate", 0.0)))
            }
        return SimulationResult(
            ok=True,
            metrics=metrics,
            findings=["finance_simulated"],
            artifacts=[],
            sources=[],
            cost_summary={"token_est": 0, "tool_runtime_ms": 0},
            spans=[],
        )
