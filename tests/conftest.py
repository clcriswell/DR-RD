import pytest
from core.llm_client import set_budget_manager


@pytest.fixture(autouse=True)
def _reset_budget():
    yield
    set_budget_manager(None)
