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
