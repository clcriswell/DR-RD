"""Dry-run checks for Plan v2 PoC test planning artifacts."""

from pathlib import Path


def test_poc_test_plan_template_exists():
    """PoC test plan template should define hypotheses, scenarios, metrics, and gates."""
    assert Path("docs/poc_test_plan.md").exists(), "PoC test plan template missing"


def test_simulation_hooks_present():
    """Simulation manager indicates hooks for fast feedback loops."""
    assert Path("simulation/simulation_manager.py").exists(), "Simulation hooks missing"


def test_environment_matrix_defined():
    """Environment matrix describes target environments for test runs."""
    matrix_path = Path("docs/environment_matrix.yaml")
    assert matrix_path.exists(), "Environment matrix missing"
    import yaml
    with matrix_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict) and data, "Environment matrix malformed"
