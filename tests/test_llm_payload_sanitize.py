import core.llm_client as llm


def test_llm_payload_sanitize():
    payload = {
        "model": "gpt-test",
        "input": [],
        "provider": "openai",
        "json_strict": True,
        "tool_use": {"a": 1},
        "temperature": 0.1,
        "extra": 42,
    }
    cleaned = llm._sanitize_responses_payload(payload)
    assert "provider" not in cleaned
    assert "json_strict" not in cleaned
    assert "tool_use" not in cleaned
    assert "extra" not in cleaned
    assert cleaned["temperature"] == 0.1
    assert set(cleaned.keys()) == {"model", "input", "temperature"}
