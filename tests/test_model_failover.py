from core.llm.model_router import ModelSpec, RouteDecision
from core.llm.clients import call_model_with_failover


def test_failover_once(monkeypatch):
    backup = ModelSpec(provider="google", name="gemini-1.5-pro", purpose=[], ctx=1000000, speed_class="medium", price_in=0.0, price_out=0.0)
    decision = RouteDecision(provider="openai", model="gpt-4.1-mini", reason="preferred", backups=[backup])
    calls = []

    def fake_call(decision, prompt_obj, timeout_ms):
        calls.append(decision.model)
        if decision.model == "gpt-4.1-mini":
            raise RuntimeError("timeout")
        return {"text": "ok"}, {"total_tokens": 1}

    monkeypatch.setattr("core.llm.clients.call_model", fake_call)
    result, usage = call_model_with_failover(decision, {}, 1000)
    assert calls == ["gpt-4.1-mini", "gemini-1.5-pro"]
    assert result["text"] == "ok"
