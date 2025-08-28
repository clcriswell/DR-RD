from dr_rd.prompting import example_selectors as es


def test_provider_packs_json_only():
    cands = [{"input": "q", "output": {"answer": 1, "reasoning": "secret"}}]
    openai_pack = es.pack_for_provider(cands, "openai", True)
    assert openai_pack["messages"][0]["role"] == "system"
    assert "reasoning" not in openai_pack["messages"][2]["content"]

    anthropic_pack = es.pack_for_provider(cands, "anthropic", True)
    assert anthropic_pack["messages"][0]["role"] == "system"
    assert "reasoning" not in anthropic_pack["messages"][2]["content"]

    gemini_pack = es.pack_for_provider(cands, "gemini", True)
    assert gemini_pack["messages"][0]["name"] == "example"
    assert "reasoning" not in gemini_pack["messages"][0]["response"]
