import pytest

from utils.agent_json import AgentOutputFormatError, extract_json_strict


def test_repair_markdown_fences():
    txt = "```json\n{\"a\":1}\n```"
    assert extract_json_strict(txt) == {"a": 1}


def test_malformed_json_raises():
    with pytest.raises(AgentOutputFormatError):
        extract_json_strict("```json\n{bad}\n```")
