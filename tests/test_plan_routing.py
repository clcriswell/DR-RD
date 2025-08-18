import importlib, sys
from types import SimpleNamespace
from unittest.mock import MagicMock


def load_app():
    st = SimpleNamespace(session_state={}, secrets={"gcp_service_account": {}}, cache_resource=lambda f: f)
    sys.modules['streamlit'] = st
    sys.modules['openai'] = MagicMock()
    if 'app' in sys.modules:
        importlib.reload(sys.modules['app'])
    else:
        importlib.import_module('app')
    return sys.modules['app']


def test_normalize_plan_formats():
    app = load_app()
    plan_a = {"CTO": [{"title": "A", "description": "B"}]}
    plan_b = [{"role": "CTO", "title": "A", "description": "B"}]
    assert app.normalize_plan_to_tasks(plan_a) == app.normalize_plan_to_tasks(plan_b)


def test_role_alias_normalization():
    app = load_app()
    assert app.normalize_role("Regulatory & Compliance Lead") == "Regulatory"


def test_unknown_role_routes_to_default():
    app = load_app()
    agents = app.get_agents()
    tasks = [{"role": "Wizard", "title": "Budget study", "description": "cost analysis"}]
    routed, dropped = app.route_tasks(tasks, agents)
    assert not dropped
    rr, agent, _ = routed[0]
    assert rr in agents
