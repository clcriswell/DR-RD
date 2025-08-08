from typing import Dict, Callable, Optional, Any
from simulation.simulation_manager import SimulationManager

from config.feature_flags import (
    SIM_OPTIMIZER_ENABLED,
    SIM_OPTIMIZER_STRATEGY,
    SIM_OPTIMIZER_MAX_EVALS,
)
from dr_rd.simulation.design_space import DesignSpace
from dr_rd.simulation.optimizer import optimize


def determine_sim_type(role: str, design_spec: str) -> str:
    """Determine which simulation to run based on the role name and design spec."""
    role = role.lower()
    if "mechanical" in role or "motion" in role:
        return "structural"
    elif "electronics" in role or "embedded" in role:
        return "electronics"
    elif "chemical" in role or "surface" in role:
        return "chemical"
    elif "thermal" in design_spec.lower():
        return "thermal"
    else:
        return ""


class SimulationAgent:
    """Agent that selects and runs simulations for design specifications."""

    def __init__(self):
        # Initialize a SimulationManager to handle simulation calls
        self.sim_manager = SimulationManager()

    def append_simulations(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Append simulation results to each role output when applicable."""
        updated = {}
        for role, spec in answers.items():
            sim_type = determine_sim_type(role, spec)
            if not sim_type:
                updated[role] = spec  # No simulation required for this role
                continue  # Skip simulation
            metrics = self.sim_manager.simulate(sim_type, spec)
            lines = [f"**Simulation ({sim_type.capitalize()}) Results:**"]
            for metric, value in metrics.items():
                if metric in ["pass", "failed"]:
                    continue  # skip internal status keys in output
                lines.append(f"- **{metric}**: {value}")
            updated[role] = f"{spec}\n\n" + "\n".join(lines)
        return updated

    def run_simulation(
        self,
        role: str,
        design_spec: str,
        design_space: Optional[DesignSpace] = None,
        objective_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], float]] = None,
        scorecard: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Run a simulation for a single role's design specification.

        When a ``design_space`` and ``objective_fn`` are provided and the
        optimizer feature flag is enabled, parameter search is performed and
        the best design is reported. When a ``scorecard`` is supplied and
        evaluator support is enabled, the optimizer will blend the simulation
        score with ``scorecard['overall']``.
        """

        sim_type = determine_sim_type(role, design_spec)
        if not sim_type:
            return ""  # No simulation needed for this role

        best_design = None
        if SIM_OPTIMIZER_ENABLED and design_space and objective_fn:
            def simulator(d: Dict[str, Any]) -> Dict[str, Any]:
                formatted = design_spec.format(**d)
                return self.sim_manager.simulate(sim_type, formatted)

            best_design, metrics = optimize(
                {},
                design_space,
                objective_fn,
                simulator,
                strategy=SIM_OPTIMIZER_STRATEGY,
                max_evals=SIM_OPTIMIZER_MAX_EVALS,
                scorecard=scorecard,
            )
        else:
            metrics = self.sim_manager.simulate(sim_type, design_spec)

        lines = [f"**Simulation ({sim_type.capitalize()}) Results:**"]
        if best_design is not None:
            lines.append(f"- **Design**: {best_design}")
        for metric, value in metrics.items():
            if metric in ["pass", "failed"]:
                continue  # skip internal status keys in output
            lines.append(f"- **{metric}**: {value}")
        return "\n".join(lines)
