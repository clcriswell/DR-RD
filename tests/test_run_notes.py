from pathlib import Path

from utils import run_notes


def test_load_save_toggle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    saved = run_notes.save("r1", title="t", note="n", tags=["a", "b"], favorite=False)
    assert saved["favorite"] is False
    loaded = run_notes.load("r1")
    assert loaded["title"] == "t"
    toggled = run_notes.toggle_favorite("r1")
    assert toggled["favorite"] is True
    notes = run_notes.all_notes()
    assert "r1" in notes


def test_clamp_and_atomic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    long_note = "x" * 20000
    many_tags = [str(i) for i in range(20)]
    saved = run_notes.save("r2", title="", note=long_note, tags=many_tags, favorite=False)
    assert len(saved["note"]) == 10000
    assert len(saved["tags"]) == 10
    path = Path(".dr_rd") / "runs" / "r2" / "notes.json"
    ino1 = path.stat().st_ino
    saved2 = run_notes.save("r2", title="a", note="b", tags=[], favorite=True)
    ino2 = path.stat().st_ino
    assert ino1 != ino2
