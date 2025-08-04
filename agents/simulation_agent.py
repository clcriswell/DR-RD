from typing import Dict
from simulation.simulation_manager import SimulationManager


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

    def run_simulation(self, role: str, design_spec: str) -> str:
        """Run a simulation for a single role's design specification."""
        sim_type = determine_sim_type(role, design_spec)
        if not sim_type:
            return ""  # No simulation needed for this role
        metrics = self.sim_manager.simulate(sim_type, design_spec)
        lines = [f"**Simulation ({sim_type.capitalize()}) Results:**"]
        for metric, value in metrics.items():
            if metric in ["pass", "failed"]:
                continue  # skip internal status keys in output
            lines.append(f"- **{metric}**: {value}")
        return "\n".join(lines)
