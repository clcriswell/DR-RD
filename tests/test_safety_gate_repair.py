from core import safety_gate
from config import feature_flags


def test_single_repair():
    out = {"msg": "openai key sk-ABCDEF1234567890ABCDEFGHI"}

    def retry():
        return {"msg": "clean"}

    ok, repaired, meta = safety_gate.guard_output("Planner", out, retry_fn=retry)
    assert ok
    assert repaired["msg"] == "clean"
    assert meta["attempts"] == 1


def test_evaluator_retry(monkeypatch):
    out = {"msg": "openai key sk-ABCDEF1234567890ABCDEFGHI"}
    attempts = {"n": 0}

    def retry():
        attempts["n"] += 1
        return {"msg": "openai key sk-ABCDEF1234567890ABCDEFGHI"}

    def evaluator_retry():
        return {"msg": "clean"}

    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", True)
    ok, repaired, meta = safety_gate.guard_output(
        "Planner", out, retry_fn=retry, evaluator_retry_fn=evaluator_retry
    )
    assert ok
    assert meta["attempts"] == 2
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)
