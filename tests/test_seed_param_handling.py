import logging

import pytest

from core import llm_client


class DummyResp:
    http_status = 200
    output = []
    output_text = "ok"


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("DRRD_USE_CHAT_FOR_SEEDED", raising=False)
    yield


def test_seed_stripped_default(monkeypatch, caplog):
    called = {}

    def fake_create(**kwargs):
        nonlocal called
        called = kwargs
        return DummyResp()

    monkeypatch.setattr(llm_client.client.responses, "create", fake_create)
    monkeypatch.setattr(
        llm_client.client.chat.completions, "create", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("chat called"))
    )
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: "ok")
    caplog.set_level(logging.INFO)
    llm_client.call_openai(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        response_params={"seed": 123},
    )
    assert "seed" not in called
    assert any("Ignoring unsupported Responses param: seed" in r.message for r in caplog.records)


def test_seed_routes_to_chat(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_USE_CHAT_FOR_SEEDED", "true")
    chat_called = {}

    def fake_chat_create(**kwargs):
        nonlocal chat_called
        chat_called = kwargs
        return DummyResp()

    monkeypatch.setattr(llm_client.client.chat.completions, "create", fake_chat_create)
    monkeypatch.setattr(
        llm_client.client.responses, "create", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("responses called"))
    )
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: "ok")
    caplog.set_level(logging.INFO)
    llm_client.call_openai(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        response_params={"seed": 42},
    )
    assert chat_called.get("seed") == 42
    assert any("Using chat.completions for seeded request" in r.message for r in caplog.records)


def test_seed_stripped_when_schema(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_USE_CHAT_FOR_SEEDED", "true")
    called = {}

    def fake_create(**kwargs):
        nonlocal called
        called = kwargs
        return DummyResp()

    monkeypatch.setattr(llm_client.client.responses, "create", fake_create)
    monkeypatch.setattr(
        llm_client.client.chat.completions, "create", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("chat called"))
    )
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: "ok")
    caplog.set_level(logging.INFO)
    llm_client.call_openai(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        response_format={"type": "json_object"},
        response_params={"seed": 99},
    )
    assert "seed" not in called
    assert any("Ignoring unsupported Responses param: seed" in r.message for r in caplog.records)
