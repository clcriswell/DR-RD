import json

from core.llm_client import call_openai, llm_call


class StubClient:
    def __init__(self, captured):
        self.captured = captured
        self.responses = self

    def create(self, **payload):
        self.captured.update(payload)
        class Resp:
            http_status = 200
            output_text = "{}"
        return Resp()


def test_payload_sanitization(monkeypatch):
    cap = {}
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("core.llm_client._client", lambda: StubClient(cap))
    call_openai(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
        response_params={"temperature": 0.5, "openai": {"foo": 1}, "anthropic": {}, "gemini": {}},
    )
    assert "openai" not in cap and "anthropic" not in cap and "gemini" not in cap


def test_response_format_enforce(monkeypatch):
    cap = {}
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("core.llm_client._client", lambda: StubClient(cap))
    monkeypatch.setattr("core.llm_client._supports_response_format", lambda: True)
    llm_call(None, "gpt-4o", "stage", [{"role": "user", "content": "hi"}], enforce_json=True)
    assert cap.get("response_format") == {"type": "json_object"}


def test_model_gating_for_search(monkeypatch):
    cap = {}
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("core.llm_client._client", lambda: StubClient(cap))
    call_openai(
        model="gpt-3.5",
        messages=[{"role": "user", "content": "hi"}],
        response_params={"tool_use": {"search": True}},
    )
    assert cap["model"] in {"gpt-4o", "gpt-4o-mini"}

