import pytest

from core.llm import select_model


@pytest.mark.parametrize(
    "ui,purpose_env,global_env,expected",
    [
        ("ui-choice", None, None, "ui-choice"),
        (None, "purpose-model", None, "purpose-model"),
        (None, None, "global-model", "global-model"),
    ],
)
def test_select_model_precedence(monkeypatch, ui, purpose_env, global_env, expected):
    monkeypatch.delenv("DRRD_FORCE_MODEL", raising=False)
    monkeypatch.delenv("DRRD_MODEL_PLANNER", raising=False)
    monkeypatch.delenv("DRRD_OPENAI_MODEL", raising=False)
    if purpose_env:
        monkeypatch.setenv("DRRD_MODEL_PLANNER", purpose_env)
    if global_env:
        monkeypatch.setenv("DRRD_OPENAI_MODEL", global_env)
    assert select_model("planner", ui) == expected


def test_select_model_forced_override(monkeypatch):
    monkeypatch.setenv("DRRD_FORCE_MODEL", "forced")
    assert select_model("planner", "ui-choice") == "forced"
