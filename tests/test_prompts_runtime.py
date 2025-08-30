import pytest
from utils.prompts import runtime


def test_defaults_and_pin():
    text, pin = runtime.render("planner", {})
    assert "Tone: concise" in text
    assert pin["id"] == "planner"
    assert pin["version"] == "1.0.0"
    assert len(pin["hash"]) == 64


def test_missing_var():
    with pytest.raises(KeyError):
        runtime.render("executor", {})
