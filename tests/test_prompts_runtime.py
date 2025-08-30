from utils.prompts import runtime


def test_defaults_and_pin():
    text, pin = runtime.render("planner", {})
    assert "Tone: concise" in text
    assert pin["id"] == "planner"
    assert pin["version"] == "1.0.0"
    assert len(pin["hash"]) == 64


def test_executor_placeholder_task():
    text, pin = runtime.render("executor", {})
    assert "Complete the task:" in text
    assert pin["id"] == "executor"


def test_executor_with_task():
    text, _ = runtime.render("executor", {"task": "do something"})
    assert "do something" in text
