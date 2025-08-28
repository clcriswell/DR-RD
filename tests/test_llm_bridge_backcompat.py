from config import feature_flags
from core.llm import select_model


def test_select_model_env_override(monkeypatch):
    monkeypatch.setenv("DRRD_MODEL_EXEC", "env-model")
    monkeypatch.setattr(feature_flags, "MODEL_ROUTING_ENABLED", False)
    assert select_model("exec") == "env-model"


def test_select_model_router(monkeypatch):
    monkeypatch.delenv("DRRD_MODEL_EXEC", raising=False)
    monkeypatch.setattr(feature_flags, "MODEL_ROUTING_ENABLED", True)
    monkeypatch.setattr(feature_flags, "BUDGET_PROFILE", "standard")
    model = select_model("exec", agent_name="Research Scientist")
    assert model == "claude-3-5-sonnet"
