import types

from core import llm_client


def test_search_model_gating(monkeypatch):
    captured = {}

    def fake_call_openai(**kwargs):
        captured.update(kwargs)
        return {"raw": types.SimpleNamespace(output_text="ok")}

    monkeypatch.setattr(llm_client, "call_openai", fake_call_openai)
    llm_client.llm_call(None, "gpt-3", "exec", [], tool_use={"search": True})
    assert captured["model"] in {"gpt-4o", "gpt-4o-mini"}


def test_param_sanitization(monkeypatch):
    captured = {}

    def fake_call_openai(**kwargs):
        captured.update(kwargs)
        return {"raw": types.SimpleNamespace(output_text="ok")}

    monkeypatch.setattr(llm_client, "call_openai", fake_call_openai)
    llm_client.llm_call(
        None,
        "gpt-4o",
        "exec",
        [],
        openai={"a": 1},
        anthropic={"b": 2},
    )
    params = captured["response_params"]
    assert "openai" not in params and "anthropic" not in params


def test_response_format(monkeypatch):
    captured = {}

    def fake_call_openai(**kwargs):
        captured.update(kwargs)
        return {"raw": types.SimpleNamespace(output_text="{}")}

    monkeypatch.setattr(llm_client, "call_openai", fake_call_openai)
    monkeypatch.setattr(llm_client, "_supports_response_format", lambda: True)
    llm_client.llm_call(None, "gpt-4o", "exec", [], enforce_json=True)
    assert captured["response_format"] == {"type": "json_object"}
