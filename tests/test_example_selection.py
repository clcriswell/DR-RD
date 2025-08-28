import json
from dr_rd.prompting import example_selectors as es
from dr_rd.examples import catalog
from dr_rd.kb import store


def test_score_candidates_ranking_and_dedupe(monkeypatch):
    es.CONFIG["EXAMPLE_RECENCY_WEIGHT"] = 0.2

    data = [
        {"task": "A", "quality_score": 0.8, "ts": 1, "input": "a", "output": {"a": 1}},
        {"task": "B", "quality_score": 0.8, "ts": 2, "input": "b", "output": {"b": 1}},
        {"task": "B", "quality_score": 0.9, "ts": 1, "input": "b2", "output": {"b": 2}},
    ]
    monkeypatch.setattr(catalog, "fetch", lambda role, n: data)
    monkeypatch.setattr(store, "query", lambda filters, limit: [])

    res = es.score_candidates("Planner", "task", "openai", 3, 100)
    assert len(res) == 2
    assert res[0]["task"] == "B"
    assert res[1]["task"] == "A"
