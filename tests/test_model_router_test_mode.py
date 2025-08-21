import importlib
import config.model_routing as mr


def test_pick_model_env_override(monkeypatch):
    monkeypatch.setenv("TEST_MODEL_ID", "cheap-env")
    importlib.reload(mr)
    assert mr.pick_model("plan", None, mode="test") == "cheap-env"


def test_pick_model_cheapest(monkeypatch):
    monkeypatch.delenv("TEST_MODEL_ID", raising=False)
    importlib.reload(mr)
    prices = {
        "exp": {"input": 1.0, "output": 1.0},
        "cheap": {"input": 0.1, "output": 0.1},
    }
    assert mr.pick_model("plan", None, mode="test", prices=prices) == "cheap"


def test_cheap_default_from_prices(monkeypatch):
    """_cheap_default should pick the lowest-cost model from the price table."""
    monkeypatch.delenv("TEST_MODEL_ID", raising=False)
    importlib.reload(mr)
    # Ensure the model chosen from the repository's price table is gpt-4-turbo.
    assert mr._cheap_default(mr.PRICE_TABLE) == "gpt-4-turbo"
    assert mr.pick_model("plan", None, mode="test") == "gpt-4-turbo"
