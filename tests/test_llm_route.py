import os
os.environ.setdefault("OPENAI_API_KEY", "test")
from unittest.mock import patch, MagicMock
import core.llm as llm
import dr_rd.llm_client as lc


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


def test_chat_route():
    fake = MagicMock()
    fake.chat.completions.create.return_value = make_chat_resp()
    with patch.object(lc, "client", fake):
        res = llm.complete("You are a test.", "Say OK.", model="gpt-4o-mini")
    assert isinstance(res.content, str)
    fake.chat.completions.create.assert_called_once()


def test_responses_route():
    fake = MagicMock()
    fake.responses.create.return_value = make_resp_resp()
    with patch.object(lc, "client", fake):
        res = llm.complete("You are a test.", "Say OK.", model="gpt-4.1")
    assert isinstance(res.content, str)
    fake.responses.create.assert_called_once()
