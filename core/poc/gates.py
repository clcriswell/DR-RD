"""Safety gates for PoC simulations."""
from .testplan import TestCase
from simulation.registry import REGISTRY


def assert_safe(test: TestCase) -> None:
    """Allow only simulations registered in REGISTRY.

    Raises:
        Exception: if the requested simulation is not registered.
    """
    sim_name = test.inputs.get("_sim")
    if not sim_name or sim_name not in REGISTRY:
        raise Exception(f"Unregistered simulation: {sim_name}")
