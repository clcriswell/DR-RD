from utils.query_params import (
    SHORTEN_IDEA,
    decode_config,
    encode_config,
    merge_into_defaults,
    view_state_from_params,
)


def test_round_trip_simple_fields():
    defaults = {
        "idea": "",
        "mode": "standard",
        "budget_limit_usd": 0.0,
        "max_tokens": 0,
        "knowledge_sources": [],
        "advanced": {},
    }
    cfg = {
        "idea": "hello",
        "mode": "deep",
        "budget_limit_usd": 2.5,
        "max_tokens": 8000,
        "knowledge_sources": ["local", "samples"],
    }
    enc = encode_config(cfg)
    dec = decode_config(enc)
    merged = merge_into_defaults(defaults, dec)
    assert merged["idea"] == "hello"
    assert merged["mode"] == "deep"
    assert isinstance(merged["budget_limit_usd"], float)
    assert isinstance(merged["max_tokens"], int)
    assert merged["knowledge_sources"] == ["local", "samples"]


def test_idea_truncation():
    long_idea = "x" * (SHORTEN_IDEA + 50)
    enc = encode_config({"idea": long_idea})
    assert len(enc["idea"]) == SHORTEN_IDEA


def test_robust_decode():
    params = {
        "budget": "notanumber",
        "max": "also_bad",
        "adv": "!!bad!!",
    }
    dec = decode_config(params)
    assert "budget_limit_usd" not in dec
    assert "max_tokens" not in dec
    assert dec.get("advanced") == {}


def test_view_state_defaults():
    vs = view_state_from_params({})
    assert vs == {"view": "run", "trace_view": "summary", "trace_query": "", "run_id": None}
    vs2 = view_state_from_params({"view": "trace", "trace_view": "raw", "q": "hello", "run_id": "rid"})
    assert vs2 == {"view": "trace", "trace_view": "raw", "trace_query": "hello", "run_id": "rid"}
