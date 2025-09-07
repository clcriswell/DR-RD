import json
from types import SimpleNamespace

import pytest

from core import llm_client
from dr_rd.telemetry.api_call_log import APICallLogger
from dr_rd.telemetry import loggers as api_loggers


class DummyResp:
    http_status = 200

    def __init__(self, text="hi"):
        self.output = []
        self.output_text = text

    def model_dump_json(self):
        return json.dumps({"text": self.output_text})


def test_logs_successful_call(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_client.client.responses, "create", lambda **_: DummyResp())
    monkeypatch.setattr(llm_client, "extract_text", lambda resp: resp.output_text)
    logger = APICallLogger("r1", tmp_path, enabled=True)
    api_loggers.set_api_call_logger(logger)
    try:
        llm_client.call_openai(
            model="m",
            messages=[{"role": "user", "content": "hi"}],
            meta={"task_id": "T1", "agent": "tester"},
        )
    finally:
        logger.flush()
        api_loggers.set_api_call_logger(None)
    rec = json.loads((tmp_path / "api_calls.jsonl").read_text().splitlines()[0])
    assert rec["prompt_text"]
    assert rec["response_text"] == DummyResp().model_dump_json()
    assert rec["error"] is False


def test_logs_exception_and_files_created(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    def boom(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(llm_client.client.responses, "create", boom)

    class BoomChat:
        def create(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(llm_client.client.chat, "completions", BoomChat())
    logger = APICallLogger("r2", tmp_path, enabled=True)
    api_loggers.set_api_call_logger(logger)
    with pytest.raises(RuntimeError):
        llm_client.call_openai(model="m", messages=[{"role": "user", "content": "hi"}])
    logger.flush()
    api_loggers.set_api_call_logger(None)
    j = tmp_path / "api_calls.jsonl"
    c = tmp_path / "api_calls.csv"
    m = tmp_path / "api_calls.md"
    assert j.exists() and c.exists() and m.exists()
    rec = json.loads(j.read_text().splitlines()[0])
    assert rec["error"] is True
    assert rec["exception"]
