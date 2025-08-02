class SimulationManager:
    """Manages different types of simulations (structural, thermal, electronics, chemical)."""
    def __init__(self):
        # Register simulation handler stubs for each simulation type
        self.simulators = {
            "structural": self._simulate_structural,
            "thermal": self._simulate_thermal,
            "electronics": self._simulate_electronics,
            "chemical": self._simulate_chemical
        }

    def simulate(self, sim_type: str, design_spec: str) -> dict:
        """Run the specified type of simulation on the given design specification.
        Returns a dictionary of performance metrics as the simulation result."""
        sim_type = sim_type.lower()
        if sim_type in self.simulators:
            return self.simulators[sim_type](design_spec)
        else:
            raise ValueError(f"Simulation type '{sim_type}' is not supported.")

    def _simulate_structural(self, design_spec: str) -> dict:
        # Stub: simulate structural analysis (e.g., load, stress)
        return {"Max Load": "1.5 tons", "Safety Factor": 3.2}

    def _simulate_thermal(self, design_spec: str) -> dict:
        # Stub: simulate thermal performance (e.g., temperature, heat dissipation)
        return {"Max Temperature": "85°C", "Heat Dissipation": "120 W"}

    def _simulate_electronics(self, design_spec: str) -> dict:
        # Stub: simulate electronics performance (e.g., power usage, speed)
        return {"Power Consumption": "50 W", "Clock Speed": "2.5 GHz"}

    def _simulate_chemical(self, design_spec: str) -> dict:
        # Stub: simulate chemical process (e.g., yield, purity)
        return {"Yield": "78%", "Purity": "95%"}
