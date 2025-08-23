import os

os.environ.setdefault("OPENAI_API_KEY", "test")
from unittest.mock import MagicMock, patch

import core.llm as llm
import core.llm_client as lc


def make_chat_resp():
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = "OK"
    resp.model_dump.return_value = {}
    return resp


def make_resp_resp():
    resp = MagicMock()
    item = MagicMock()
    item.type = "message"
    content = MagicMock()
    content.type = "output_text"
    content.text = "OK"
    item.content = [content]
    resp.output = [item]
    resp.model_dump.return_value = {}
    return resp


def test_responses_route():
    fake = MagicMock()
    fake.responses.create.return_value = make_resp_resp()
    with patch.object(lc, "client", fake):
        res = llm.complete("You are a test.", "Say OK.", model="gpt-5")
    assert isinstance(res.content, str)
    fake.responses.create.assert_called_once()


def test_responses_drops_temperature():
    fake = MagicMock()
    fake.responses.create.return_value = make_resp_resp()
    with patch.object(lc, "client", fake):
        res = llm.complete("You are a test.", "Say OK.", model="gpt-5", temperature=0.9)
    assert isinstance(res.content, str)
    fake.responses.create.assert_called_once()
    assert "temperature" not in fake.responses.create.call_args.kwargs
