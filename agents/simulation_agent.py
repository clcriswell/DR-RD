from simulation.simulation_manager import SimulationManager

class SimulationAgent:
    """Agent that selects and runs the appropriate simulation for a given role's design."""
    def __init__(self):
        # Initialize a SimulationManager to handle simulation calls
        self.sim_manager = SimulationManager()

    def run_simulation(self, role: str, design_spec: str) -> str:
        """
        Determine the simulation type based on the role or content, run the simulation,
        and return the results formatted as Markdown.
        """
        # Decide simulation type by role (or design content for Research Scientist)
        role_lower = role.lower()
        if "engineer" in role_lower:
            sim_type = "structural"
        elif "cto" in role_lower:
            sim_type = "electronics"
        elif "research scientist" in role_lower:
            # Heuristic: choose thermal vs chemical based on keywords in the design spec
            spec_lower = design_spec.lower()
            if any(term in spec_lower for term in ["chemical", "chemistry", "compound", "reaction", "material"]):
                sim_type = "chemical"
            else:
                sim_type = "thermal"
        else:
            # Roles without a designated simulation type
            return ""

        # Run the chosen simulation and get metrics
        metrics = self.sim_manager.simulate(sim_type, design_spec)
        # Format the metrics as a Markdown section
        lines = [f"**Simulation ({sim_type.capitalize()}) Results:**"]
        for metric, value in metrics.items():
            lines.append(f"- **{metric}**: {value}")
        return "\n".join(lines)
