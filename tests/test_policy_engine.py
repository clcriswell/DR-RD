from dr_rd.policy import engine


def test_policy_decision():
    text = "Email me at test@example.com and use AWS key AKIA1234567890ABCDEF"
    classes = engine.classify(text)
    assert "pii" in classes and "secrets" in classes
    decision = engine.evaluate(text)
    assert not decision.allowed
    assert "secrets" in decision.violations
    assert "pii" in decision.redactions
