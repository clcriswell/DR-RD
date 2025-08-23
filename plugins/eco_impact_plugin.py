"""Sustainability metrics plugin.

This module implements :class:`EcoImpactPlugin`, a simple plugin that
estimates energy usage, carbon footprint and recyclability metrics based
on keyword heuristics.
"""

from __future__ import annotations

from plugins.plugin_base import Plugin


class EcoImpactPlugin(Plugin):
    """Plugin to simulate sustainability metrics based on project content.

    Examples
    --------
    >>> plugin = EcoImpactPlugin()
    >>> plugin.run("Develop a green software platform")  # doctest: +SKIP
    {'Energy Usage': '50 kWh/year', 'Carbon Footprint': '20 kg CO2/year', 'Recyclability': '90%'}
    """

    def __init__(self) -> None:
        """Initialize the plugin with identifying metadata."""
        super().__init__()
        self.name = "eco_impact"
        self.description = "Estimates environmental impact metrics (energy use, carbon footprint, recyclability)."

    def run(self, task: str, context: str = ""):
        """Analyze the given text and return sustainability metrics.

        Parameters
        ----------
        task:
            Description of the project task.
        context:
            Additional context or details about the project.

        Returns
        -------
        dict[str, str]
            Mapping of metric name to human-readable value.

        Examples
        --------
        >>> plugin = EcoImpactPlugin()
        >>> plugin.run("Design an AI data center")  # doctest: +SKIP
        {'Energy Usage': '1000 kWh/year', 'Carbon Footprint': '500 kg CO2/year', 'Recyclability': '20%'}
        """
        text = f"{task} {context}".lower()
        # Define keyword heuristics for energy usage categories
        high_energy_keywords = [
            "ai",
            "machine learning",
            "data center",
            "blockchain",
            "cloud",
            "mining",
        ]
        moderate_energy_keywords = ["device", "hardware", "robot", "manufactur"]
        low_energy_keywords = ["software", "app", "service", "platform"]
        # Default categories
        energy_level = "Moderate"
        carbon_level = "Moderate"
        recycle_level = "Moderate"
        # Determine energy/carbon levels based on keywords
        if any(term in text for term in high_energy_keywords):
            energy_level = "High"
            carbon_level = "High"
            recycle_level = "Low"
        elif any(term in text for term in moderate_energy_keywords):
            energy_level = "Moderate"
            carbon_level = "Moderate"
            recycle_level = "Moderate"
        elif any(term in text for term in low_energy_keywords):
            energy_level = "Low"
            carbon_level = "Low"
            recycle_level = "High"
        # Adjust metrics if explicitly sustainable terms present
        if any(term in text for term in ["sustainable", "renewable", "green"]):
            if energy_level == "High":
                energy_level = "Moderate"
            if carbon_level == "High":
                carbon_level = "Moderate"
            recycle_level = "High"
        # Assign numeric values for each level (simulated)
        energy_usage = (
            "50 kWh/year"
            if energy_level == "Low"
            else ("200 kWh/year" if energy_level == "Moderate" else "1000 kWh/year")
        )
        carbon_fp = (
            "20 kg CO2/year"
            if carbon_level == "Low"
            else (
                "100 kg CO2/year" if carbon_level == "Moderate" else "500 kg CO2/year"
            )
        )
        recyclability = (
            "90%"
            if recycle_level == "High"
            else ("50%" if recycle_level == "Moderate" else "20%")
        )
        # Return a dictionary of metrics
        return {
            "Energy Usage": energy_usage,
            "Carbon Footprint": carbon_fp,
            "Recyclability": recyclability,
        }
