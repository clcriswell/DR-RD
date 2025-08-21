import logging
import re

import pytest

from core import llm_client


class DummyResp:
    http_status = 200
    output = []
    output_text = "hi"


def test_llm_logging_success(monkeypatch, caplog):
    monkeypatch.setattr(
        llm_client.client.responses,
        "create",
        lambda **kwargs: DummyResp(),
    )
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: "hi")
    caplog.set_level(logging.INFO)
    llm_client.call_openai(model="m", messages=[{"role": "user", "content": "hi"}])
    starts = [r for r in caplog.records if r.message.startswith("LLM start")]
    ends = [r for r in caplog.records if r.message.startswith("LLM end")]
    assert len(starts) == 1 and len(ends) == 1
    rid_start = re.search(r"req=([0-9a-f]+)", starts[0].message).group(1)
    rid_end = re.search(r"req=([0-9a-f]+)", ends[0].message).group(1)
    assert rid_start == rid_end
    assert "status=200" in ends[0].message
    duration = int(re.search(r"duration_ms=(\d+)", ends[0].message).group(1))
    assert duration >= 0


def test_llm_logging_exception(monkeypatch, caplog):
    def boom(**kwargs):
        raise RuntimeError("404 boom")

    monkeypatch.setattr(llm_client.client.responses, "create", boom)

    class BoomChat:
        def create(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(llm_client.client.chat, "completions", BoomChat())
    caplog.set_level(logging.INFO)
    with pytest.raises(RuntimeError):
        llm_client.call_openai(model="m", messages=[{"role": "user", "content": "hi"}])
    starts = [r for r in caplog.records if r.message.startswith("LLM start")]
    ends = [r for r in caplog.records if r.message.startswith("LLM end")]
    assert len(starts) == 1 and len(ends) == 1
    rid_start = re.search(r"req=([0-9a-f]+)", starts[0].message).group(1)
    rid_end = re.search(r"req=([0-9a-f]+)", ends[0].message).group(1)
    assert rid_start == rid_end
    assert "status=EXC" in ends[0].message
