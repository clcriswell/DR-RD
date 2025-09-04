import types

from dr_rd.agents.dynamic_agent import DynamicAgent, EmptyModelOutput


def test_validate_dict_passthrough():
    agent = DynamicAgent("gpt")
    schema = {"type": "object"}
    resp = {"ok": 1}
    assert agent._validate(resp, schema, "r", "t", None, None) == {"ok": 1}


def test_validate_with_preamble():
    agent = DynamicAgent("gpt")
    schema = {"type": "object"}
    resp = types.SimpleNamespace(output_text="preamble {\"ok\":1}")
    data = agent._validate(resp, schema, "r", "t", None, None)
    assert data["ok"] == 1


def test_validate_empty_raises():
    agent = DynamicAgent("gpt")
    schema = {"type": "object"}
    resp = types.SimpleNamespace(output_text="")
    try:
        agent._validate(resp, schema, "r", "t", None, None)
    except EmptyModelOutput as e:
        assert e.payload["error"] == "empty"
    else:
        assert False, "expected EmptyModelOutput"
