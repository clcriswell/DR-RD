import types

import pytest
from openai import APIStatusError

import core.llm_client as lc


class DummyResp:
    def __init__(self):
        self.output = []
        self.usage = types.SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2)


def test_retry_on_429(monkeypatch):
    calls = {
        "count": 0,
    }

    def raise_then_succeed(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise APIStatusError(message="err", response=None, body=None, status_code=429)
        return DummyResp()

    monkeypatch.setattr(lc.client.responses, "create", raise_then_succeed)
    result = lc.call_openai(model="gpt-5", messages=[{"role": "user", "content": "hi"}])
    assert calls["count"] == 3
    assert "raw" in result
