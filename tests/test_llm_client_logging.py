import logging
import re

import pytest

from core import llm_client


class DummyResp:
    http_status = 200
    output = []


def test_logging_includes_request_id(monkeypatch, caplog):
    monkeypatch.setattr(llm_client.client.responses, "create", lambda **kwargs: DummyResp())
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: "hi")
    caplog.set_level(logging.INFO)
    llm_client.call_openai(model="m", messages=[{"role": "user", "content": "hi"}], meta={"purpose": "p", "agent": "a"})
    start = next(r.message for r in caplog.records if r.message.startswith("LLM start"))
    end = next(r.message for r in caplog.records if r.message.startswith("LLM end"))
    rid_start = re.search(r"req=([0-9a-f]+)", start).group(1)
    rid_end = re.search(r"req=([0-9a-f]+)", end).group(1)
    assert rid_start == rid_end
    duration = int(re.search(r"duration_ms=(\d+)", end).group(1))
    assert duration >= 0
