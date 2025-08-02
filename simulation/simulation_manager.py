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
        """
        Run the specified type of simulation on the given design specification.
        Returns a dictionary of performance metrics, including a boolean pass/fail and list of failed criteria.
        """
        sim_type = sim_type.lower()
        if sim_type in self.simulators:
            metrics = self.simulators[sim_type](design_spec)
        else:
            raise ValueError(f"Simulation type '{sim_type}' is not supported.")

        # Determine pass/fail criteria for each simulation type (simple threshold checks as examples)
        failed_criteria = []
        if sim_type == "structural":
            # Example: require Safety Factor >= 2.0
            try:
                sf = float(str(metrics.get("Safety Factor", "")).replace(",", ""))
            except ValueError:
                sf = None
            if sf is not None and sf < 2.0:
                failed_criteria.append("Safety Factor")
        if sim_type == "thermal":
            # Example: require Max Temperature <= 80°C
            max_temp_val = metrics.get("Max Temperature")
            if max_temp_val:
                try:
                    # Extract numeric value (assumes format like "85°C")
                    num = float(str(max_temp_val).replace("°C", "").strip())
                except ValueError:
                    num = None
                if num is not None and num > 80.0:
                    failed_criteria.append("Cooling Load" if "Max Temperature" in metrics else "Thermal Limit")
            # (We use "Cooling Load" as a named criterion for failing temperature)
        if sim_type == "electronics":
            # Example: require Power Consumption <= 100 W
            power = metrics.get("Power Consumption")
            if power:
                try:
                    val = float(str(power).replace("W", "").strip())
                except ValueError:
                    val = None
                if val is not None and val > 100.0:
                    failed_criteria.append("Power Consumption")
        if sim_type == "chemical":
            # Example: require Yield >= 80%
            yield_val = metrics.get("Yield")
            if yield_val:
                try:
                    num = float(str(yield_val).replace("%", "").strip())
                except ValueError:
                    num = None
                if num is not None and num < 80.0:
                    failed_criteria.append("Yield")

        # Set pass status
        pass_status = (len(failed_criteria) == 0)

        # Include pass and failed criteria in the result
        metrics["pass"] = pass_status
        metrics["failed"] = failed_criteria
        return metrics

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
