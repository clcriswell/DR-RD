import types

from core import llm_client


def test_llm_payload_sanitize(monkeypatch):
    captured = {}

    class DummyResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output=[], http_status=200)

    class DummyClient:
        responses = DummyResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(llm_client, "_client", lambda: DummyClient())

    llm_client.call_openai(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        response_params={
            "provider": "p",
            "json_strict": True,
            "tool_use": "none",
            "extra_keys": 1,
        },
    )

    assert "provider" not in captured
    assert "json_strict" not in captured
    assert "tool_use" not in captured
    assert "extra_keys" not in captured
    assert "input" in captured
    assert "messages" not in captured
