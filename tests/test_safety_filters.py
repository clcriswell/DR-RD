import json
from dr_rd.examples import safety_filters as sf


def test_filter_and_redact():
    policies = sf.load_policies()
    cands = [
        {"input": "ok", "output": {"a": 1}},
        {"input": "email me test@example.com", "output": {"a": 2}},
        {"input": "see http://bad.com", "output": {"a": 3}},
        {"input": "secret sk-1234567890", "output": {"a": 4}},
    ]
    res = sf.filter_and_redact(cands, policies)
    assert len(res) == 2
    assert res[0]["input"] == "ok"
    assert "[REDACTED]" in res[1]["input"]
    json.dumps(res[1]["output"])  # still JSON
