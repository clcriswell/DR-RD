from utils.eval import scoring


SPEC = {
    "id": "t1",
    "expected_keywords": ["foo", "bar"],
    "forbidden_keywords": ["bad"],
    "min_words": 1,
    "max_words": 10,
}


def test_heuristics_and_penalties():
    meta = {"status": "success"}
    out = scoring.score_item("foo baz", meta, SPEC)
    assert out["heuristic"] == 0.5
    out2 = scoring.score_item("foo bad", meta, SPEC)
    assert out2["heuristic"] == 0
    assert "forbidden" in out2["flags"]
    out3 = scoring.score_item("", {"status": "error"}, SPEC)
    assert out3["heuristic"] == 0
    assert "error" in out3["flags"]


def test_llm_path_skipped(monkeypatch):
    monkeypatch.setenv("NO_NET", "1")
    meta = {"status": "success"}
    spec = {**SPEC, "rubric": "score"}
    out = scoring.score_item("foo", meta, spec, use_llm=True)
    assert out["llm"] is None
    assert out["final"] == out["heuristic"]
