import types
import sys

from utils import validate_providers


def test_no_net(monkeypatch):
    monkeypatch.setenv("NO_NET", "1")
    out = validate_providers.quick_probe("openai", "gpt-4o-mini")
    assert out["status"] == "skip"


def test_probe_mock(monkeypatch):
    monkeypatch.delenv("NO_NET", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    class FakeClient:
        def __init__(self, *a, **k):
            self.models = self

        def retrieve(self, model):
            return {"id": model}

    openai_mod = types.SimpleNamespace(OpenAI=FakeClient)
    monkeypatch.setitem(sys.modules, "openai", openai_mod)
    out = validate_providers.quick_probe("openai", "m")
    assert out["status"] == "pass"

    class BoomClient(FakeClient):
        def __init__(self, *a, **k):
            raise RuntimeError("boom")

    openai_mod2 = types.SimpleNamespace(OpenAI=BoomClient)
    monkeypatch.setitem(sys.modules, "openai", openai_mod2)
    out = validate_providers.quick_probe("openai", "m")
    assert out["status"] == "fail"
