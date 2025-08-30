import pytest

from utils import global_search as gs


def _setup(monkeypatch):
    runs = [
        {"run_id": "r1", "idea_preview": "alpha", "started_at": 1},
        {"run_id": "r2", "idea_preview": "beta", "started_at": 2},
    ]
    notes = {
        "r1": {"title": "first", "note": "", "tags": ["a"], "favorite": False},
        "r2": {"title": "second", "note": "", "tags": ["b"], "favorite": False},
    }
    knowledge = [{"id": "k1", "name": "doc1", "tags": ["ref"], "type": "PDF"}]
    monkeypatch.setattr(gs.runs_index, "load_index", lambda: runs)
    monkeypatch.setattr(gs.run_notes, "all_notes", lambda: notes)
    monkeypatch.setattr(gs.knowledge_store, "list_items", lambda: knowledge)
    monkeypatch.setattr(
        gs,
        "default_actions",
        lambda: [
            {
                "kind": "page",
                "id": "trace",
                "label": "Trace",
                "hint": "Open page",
                "payload": {"page": "pages/10_Trace.py"},
                "text": "trace page",
            },
            {
                "kind": "cmd",
                "id": "start_demo",
                "label": "Start demo run",
                "hint": "",
                "payload": {},
                "text": "start demo",
            },
        ],
    )


def test_search_trace(monkeypatch):
    _setup(monkeypatch)
    res = gs.search("trace")
    assert res
    assert res[0]["kind"] in {"page", "run"}


def test_search_run_id(monkeypatch):
    _setup(monkeypatch)
    res = gs.search("r2")
    assert res
    assert res[0]["id"].startswith("r2")
    assert res[0]["score"] >= 0.9


def test_resolve_action():
    assert gs.resolve_action({"kind": "page", "payload": {"page": "app.py"}})["action"] == "switch_page"
    assert gs.resolve_action({"kind": "run", "payload": {"view": "trace", "run_id": "r1"}})["action"] == "set_params"
    assert (
        gs.resolve_action({"kind": "knowledge", "payload": {"item_id": "k1"}})["params"]["use_source"]
        == "k1"
    )
    assert gs.resolve_action({"kind": "cmd", "id": "start_demo", "payload": {}})["action"] == "start_demo"
