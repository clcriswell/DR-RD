import os


def test_poc_test_plan_template_exists():
    assert os.path.exists("docs/poc_test_plan.md"), "PoC test plan template missing"


def test_simulation_hooks_exist():
    assert os.path.exists("simulation/hooks.py"), "Simulation hooks missing"


def test_environment_matrix_defined():
    assert os.path.exists("config/environment_matrix.yaml"), "Environment matrix missing"
