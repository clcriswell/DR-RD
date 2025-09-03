from core import llm_client


class DummyResp:
    http_status = 200
    output = []
    output_text = ""


class DummyClient:
    def __init__(self):
        self.responses = self

    def create(self, **payload):
        self.payload = payload
        return DummyResp()


def test_llm_payload_sanitization(monkeypatch):
    dummy = DummyClient()
    monkeypatch.setattr(llm_client, "_client", lambda: dummy)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(llm_client, "load_config", lambda: {})
    llm_client.call_openai(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        provider="openai",
        json_strict=True,
        tool_use="auto",
        extra_keys="x",
    )
    payload = dummy.payload
    assert "provider" not in payload
    assert "json_strict" not in payload
    assert "tool_use" not in payload
    assert "extra_keys" not in payload
    assert "input" in payload
