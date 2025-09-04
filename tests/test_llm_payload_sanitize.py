import core.llm_client as llm_client


class DummyResp:
    http_status = 200
    output = []


def test_llm_payload_sanitize(monkeypatch):
    recorded = {}

    class DummyResponses:
        def create(self, **kwargs):
            recorded.update(kwargs)
            return DummyResp()

    class DummyClient:
        responses = DummyResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(llm_client, "_client", lambda: DummyClient())
    monkeypatch.setattr(llm_client, "_supports_response_format", lambda: True)

    messages = [{"role": "user", "content": "hi"}]
    llm_client.call_openai(
        model="gpt-4o-mini",
        messages=messages,
        response_params={
            "provider": "x",
            "json_strict": True,
            "tool_use": "auto",
            "extra_keys": "ignored",
            "max_output_tokens": 5,
        },
        tools=[{"type": "json_schema", "function": {"name": "f", "parameters": {"type": "object"}}}],
        tool_choice="auto",
        response_format={"type": "json_object"},
    )

    assert "provider" not in recorded
    assert "json_strict" not in recorded
    assert "tool_use" not in recorded
    assert "extra_keys" not in recorded
    assert recorded["model"] == "gpt-4o-mini"
    assert recorded["max_output_tokens"] == 5
    assert "input" in recorded
    assert "response_format" in recorded
    assert "tools" in recorded and recorded["tool_choice"] == "auto"
