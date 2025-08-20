import os
from unittest.mock import Mock, patch

from pathlib import Path
import yaml
from core.budget import BudgetManager
from dr_rd.utils.llm_client import llm_call, set_budget_manager


def load_prices():
    with open(Path("config") / "prices.yaml") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("models", {})


class DummyResp:
    def __init__(self):
        usage = {"prompt_tokens": 100, "completion_tokens": 100}
        self.choices = [Mock(message=Mock(content="ok"), usage=usage)]


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_budget_no_fallback():
    prices = {"models": load_prices()}
    bm = BudgetManager({"target_cost_usd": 0.0005, "stage_weights": {"exec": 1.0}}, prices)
    set_budget_manager(bm)
    mock_create = Mock(return_value=DummyResp())
    client = Mock(chat=Mock(completions=Mock(create=mock_create)))
    with patch("dr_rd.utils.llm_client.st.session_state", {}):
        llm_call(
            client,
            "gpt-4o",
            stage="exec",
            messages=[{"role": "user", "content": "hi"}],
        )
    assert mock_create.call_args[1]["model"] == "gpt-4o"


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_budget_does_not_raise():
    prices = {"models": load_prices()}
    bm = BudgetManager({"target_cost_usd": 1e-6, "stage_weights": {"exec": 1.0}}, prices)
    set_budget_manager(bm)
    mock_create = Mock(return_value=DummyResp())
    client = Mock(chat=Mock(completions=Mock(create=mock_create)))
    with patch("dr_rd.utils.llm_client.st.session_state", {}):
        llm_call(
            client,
            "gpt-3.5-turbo",
            stage="exec",
            messages=[{"role": "user", "content": "hi"}],
        )
    assert bm.spend > 0
