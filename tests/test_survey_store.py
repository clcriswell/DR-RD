import time

from utils import survey_store


def test_save_and_load(tmp_path, monkeypatch):
    path = tmp_path / "surveys.jsonl"
    monkeypatch.setattr(survey_store, "SURVEYS_PATH", path)
    survey_store.SURVEYS_PATH.parent.mkdir(parents=True, exist_ok=True)

    answers = {f"sus_q{i}": 3 for i in range(1, 11)}
    survey_store.save_sus("run1", answers, 50, None)
    survey_store.save_seq("run1", 6, "great")
    records = survey_store.load_recent()
    assert len(records) == 2
    assert {r["instrument"] for r in records} == {"SUS", "SEQ"}


def test_compute_aggregates():
    now = time.time()
    records = [
        {"ts": now, "instrument": "SUS", "total": 80},
        {"ts": now - 9 * 86400, "instrument": "SUS", "total": 60},
        {"ts": now, "instrument": "SEQ", "answers": {"score": 6}},
        {"ts": now - 9 * 86400, "instrument": "SEQ", "answers": {"score": 3}},
    ]
    stats = survey_store.compute_aggregates(records)
    assert stats["sus_count"] == 2
    assert stats["sus_mean"] == 70
    assert stats["sus_7_day_mean"] == 80
    assert stats["seq_count"] == 2
    assert stats["seq_mean"] == 4.5
    assert stats["seq_7_day_mean"] == 6
