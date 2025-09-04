import json
import pytest

from dr_rd.agents.dynamic_agent import DynamicAgent, EmptyModelOutput


class Obj:
    def __init__(self, text: str):
        self.output_text = text


def make_agent() -> DynamicAgent:
    return DynamicAgent("gpt-4o")


def test_validate_dict_passthrough():
    agent = make_agent()
    resp = {"a": 1}
    data = agent._validate(resp, {"type": "object"}, "r", "t", None, None)
    assert data["a"] == 1


def test_validate_json_with_preamble():
    agent = make_agent()
    resp = Obj("note: {\"a\":1}")
    data = agent._validate(resp, {"type": "object"}, "r", "t", None, None)
    assert data["a"] == 1


def test_validate_empty_output():
    agent = make_agent()
    resp = Obj("   ")
    with pytest.raises(EmptyModelOutput):
        agent._validate(resp, {"type": "object"}, "r", "t", None, None)

